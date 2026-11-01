using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace RemasteredCE;

public sealed class ModForm : Form
{
	private readonly string game;

	private readonly string settings;

	private readonly string sessionRoot;

	private readonly string[] forwarded;

	private readonly DataGridView grid = new DataGridView();

	private readonly ComboBox profiles = new ComboBox();

	private readonly Label status = new Label();

	private readonly Label summary = new Label();

	private readonly Button play = new Button();

	private readonly CheckBox existingScript = new CheckBox();

	private readonly List<Control> actions = new List<Control>();

	private List<ModPack> packs = new List<ModPack>();

	private ModProfile profile = new ModProfile();

	private bool busy;

	private bool rendering;

	public bool IsBusy => busy;

	public event Action<bool> BusyChanged;

	public void SaveCurrentProfile()
	{
		Save();
	}

	public void ConfigureCompact()
	{
		TableLayoutPanel tableLayoutPanel = Controls.OfType<TableLayoutPanel>().Single();
		tableLayoutPanel.Padding = new Padding(18, 12, 18, 16);
		tableLayoutPanel.RowStyles[0].Height = 40f;
		Label label = (Label)tableLayoutPanel.GetControlFromPosition(0, 0);
		label.Text = "MODS / PLAY";
		label.Font = new Font("Segoe UI Semibold", 14f);
	}

	public ModForm(string gameFolder, string[] arguments = null, bool preview = false)
	{
		game = Path.GetFullPath(gameFolder);
		settings = (preview ? Path.Combine(game, "preview-settings") : Mods.SettingsRoot(game));
		sessionRoot = (preview ? Path.Combine(game, "preview-sessions") : Mods.SessionRoot);
		forwarded = arguments ?? new string[0];
		Text = "Remastered CE â€” Mods & Launch";
		ClientSize = new Size(1100, 730);
		MinimumSize = new Size(880, 620);
		Font = new Font("Segoe UI", 10f);
		AutoScaleMode = AutoScaleMode.Dpi;
		StartPosition = FormStartPosition.CenterScreen;
		BackColor = Color.FromArgb(23, 27, 30);
		ForeColor = Color.FromArgb(235, 239, 240);
		TableLayoutPanel tableLayoutPanel = new TableLayoutPanel
		{
			Dock = DockStyle.Fill,
			ColumnCount = 1,
			RowCount = 7,
			Padding = new Padding(22)
		};
		tableLayoutPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 56f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 45f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 45f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 40f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 90f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 55f));
		Controls.Add(tableLayoutPanel);
		tableLayoutPanel.Controls.Add(new Label
		{
			Text = "REMASTERED CE",
			Font = new Font("Segoe UI Semibold", 22f),
			Dock = DockStyle.Fill,
			TextAlign = ContentAlignment.MiddleLeft
		});
		FlowLayoutPanel flowLayoutPanel = new FlowLayoutPanel
		{
			Dock = DockStyle.Fill,
			WrapContents = false
		};
		flowLayoutPanel.Controls.Add(new Label
		{
			Text = "Profile",
			AutoSize = true,
			Padding = new Padding(0, 8, 8, 0)
		});
		profiles.Width = 280;
		profiles.DropDownStyle = ComboBoxStyle.DropDown;
		flowLayoutPanel.Controls.Add(profiles);
		actions.Add(profiles);
		Add(flowLayoutPanel, "Save profile", () =>
		{
			Save();
		});
		Add(flowLayoutPanel, "New profile", () =>
		{
			CaptureState();
			profile = new ModProfile
			{
				Name = "New profile",
				Folders = profile.Folders
			};
			profiles.SelectedIndex = -1;
			profiles.Text = profile.Name;
			existingScript.Checked = false;
			foreach (ModPack pack in packs)
			{
				pack.Enabled = pack.AutoLoaded;
			}
			Render();
		});
		Add(flowLayoutPanel, "Patch only", () =>
		{
			existingScript.Checked = false;
			foreach (ModPack pack2 in packs)
			{
				pack2.Enabled = pack2.AutoLoaded;
			}
			Render();
		});
		tableLayoutPanel.Controls.Add(flowLayoutPanel);
		flowLayoutPanel = new FlowLayoutPanel
		{
			Dock = DockStyle.Fill,
			WrapContents = false
		};
		Add(flowLayoutPanel, "Refresh", async () =>
		{
			await RefreshMods();
		});
		Add(flowLayoutPanel, "Add folderâ€¦", () =>
		{
			using FolderBrowserDialog folderBrowserDialog = new FolderBrowserDialog
			{
				Description = "Choose a local or Steam Workshop mods folder"
			};
			if (folderBrowserDialog.ShowDialog(this) == DialogResult.OK)
			{
				profile.Folders = profile.Folders.Concat(new string[1] { folderBrowserDialog.SelectedPath }).Distinct(Mods.Names).ToArray();
				RefreshMods().GetAwaiter();
			}
		});
		Add(flowLayoutPanel, "Open mods folder", () =>
		{
			OpenMods();
		});
		Add(flowLayoutPanel, "Auto-sort", () =>
		{
			packs = Mods.AutoSort(packs.Where((ModPack p) => p.Enabled)).Concat(packs.Where((ModPack p) => !p.Enabled).OrderBy((ModPack p) => p.Name, Mods.Names)).ToList();
			Render();
		});
		Add(flowLayoutPanel, "Move up", () =>
		{
			MoveSelection(-1);
		});
		Add(flowLayoutPanel, "Move down", () =>
		{
			MoveSelection(1);
		});
		Add(flowLayoutPanel, "Copy mod list", async () =>
		{
			await CopyManifest();
		});
		tableLayoutPanel.Controls.Add(flowLayoutPanel);
		tableLayoutPanel.Controls.Add(new Label
		{
			Text = "Script order. Auto-sort uses declared dependencies; movie packs retain engine priority.",
			Dock = DockStyle.Fill,
			TextAlign = ContentAlignment.MiddleLeft
		});
		grid.Dock = DockStyle.Fill;
		grid.AllowUserToAddRows = false;
		grid.AllowUserToDeleteRows = false;
		grid.AllowUserToResizeRows = false;
		grid.RowHeadersVisible = false;
		grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
		grid.MultiSelect = false;
		grid.BackgroundColor = Color.FromArgb(32, 39, 43);
		grid.AutoGenerateColumns = false;
		grid.AutoSizeRowsMode = DataGridViewAutoSizeRowsMode.AllCells;
		grid.Columns.Add(new DataGridViewCheckBoxColumn
		{
			Name = "Enabled",
			HeaderText = "Use",
			Width = 44
		});
		grid.Columns.Add(new DataGridViewTextBoxColumn
		{
			Name = "Order",
			HeaderText = "Order",
			Width = 65,
			ReadOnly = true
		});
		grid.Columns.Add(new DataGridViewTextBoxColumn
		{
			Name = "Pack",
			HeaderText = "Mod / pack file",
			AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill,
			FillWeight = 45f,
			ReadOnly = true
		});
		grid.Columns.Add(new DataGridViewTextBoxColumn
		{
			Name = "Source",
			HeaderText = "Location",
			AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill,
			FillWeight = 25f,
			ReadOnly = true
		});
		grid.Columns.Add(new DataGridViewTextBoxColumn
		{
			Name = "Details",
			HeaderText = "Status / dependencies",
			AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill,
			FillWeight = 40f,
			ReadOnly = true
		});
		grid.EnableHeadersVisualStyles = false;
		grid.ColumnHeadersDefaultCellStyle.BackColor = Color.FromArgb(40, 48, 53);
		grid.ColumnHeadersDefaultCellStyle.ForeColor = ForeColor;
		grid.ColumnHeadersDefaultCellStyle.SelectionBackColor = Color.FromArgb(49, 117, 98);
		grid.ColumnHeadersDefaultCellStyle.SelectionForeColor = ForeColor;
		grid.GridColor = Color.FromArgb(72, 85, 91);
		grid.DefaultCellStyle.BackColor = Color.FromArgb(40, 48, 53);
		grid.DefaultCellStyle.ForeColor = ForeColor;
		grid.DefaultCellStyle.SelectionBackColor = Color.FromArgb(49, 117, 98);
		grid.DefaultCellStyle.SelectionForeColor = Color.White;
		grid.DefaultCellStyle.WrapMode = DataGridViewTriState.True;
		foreach (DataGridViewColumn column in grid.Columns)
		{
			column.SortMode = DataGridViewColumnSortMode.NotSortable;
		}
		grid.CurrentCellDirtyStateChanged += (object s, EventArgs e) =>
		{
			if (grid.IsCurrentCellDirty)
			{
				grid.CommitEdit(DataGridViewDataErrorContexts.Commit);
			}
		};
		grid.CellValueChanged += (object s, DataGridViewCellEventArgs e) =>
		{
			if (!rendering && e.RowIndex >= 0 && e.ColumnIndex == 0)
			{
				ModPack modPack = (ModPack)grid.Rows[e.RowIndex].Tag;
				modPack.Enabled = modPack.AutoLoaded || Convert.ToBoolean(grid.Rows[e.RowIndex].Cells[0].Value);
				UpdateSummary();
			}
		};
		tableLayoutPanel.Controls.Add(grid);
		TableLayoutPanel tableLayoutPanel2 = new TableLayoutPanel
		{
			Dock = DockStyle.Fill,
			ColumnCount = 1,
			RowCount = 2
		};
		tableLayoutPanel2.RowStyles.Add(new RowStyle(SizeType.Percent, 65f));
		tableLayoutPanel2.RowStyles.Add(new RowStyle(SizeType.Percent, 35f));
		summary.Dock = DockStyle.Fill;
		summary.Padding = new Padding(0, 7, 0, 0);
		tableLayoutPanel2.Controls.Add(summary);
		status.Dock = DockStyle.Fill;
		status.ForeColor = Color.FromArgb(158, 176, 181);
		tableLayoutPanel2.Controls.Add(status);
		tableLayoutPanel.Controls.Add(tableLayoutPanel2);
		TableLayoutPanel tableLayoutPanel3 = new TableLayoutPanel
		{
			Dock = DockStyle.Fill,
			ColumnCount = 2,
			RowCount = 1
		};
		tableLayoutPanel3.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
		tableLayoutPanel3.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 236f));
		play.Text = "Play Remastered CE";
		play.Size = new Size(230, 42);
		play.BackColor = Color.FromArgb(49, 117, 98);
		play.ForeColor = Color.White;
		play.FlatStyle = FlatStyle.Flat;
		play.FlatAppearance.BorderColor = Color.FromArgb(72, 85, 91);
		play.Click += async (object s, EventArgs e) =>
		{
			await Play();
		};
		tableLayoutPanel3.Controls.Add(play, 1, 0);
		existingScript.Text = "Use existing user.script.txt (ignore selections)";
		existingScript.Dock = DockStyle.Fill;
		existingScript.CheckedChanged += (sender, e) =>
		{
			grid.Enabled = !busy && !existingScript.Checked;
			play.Text = existingScript.Checked ? "Play existing script" : "Play Remastered CE";
		};
		actions.Add(existingScript);
		tableLayoutPanel3.Controls.Add(existingScript, 0, 0);
		tableLayoutPanel.Controls.Add(tableLayoutPanel3);
		profiles.SelectionChangeCommitted += async (object s, EventArgs e) =>
		{
			if (profiles.SelectedItem is ModProfile)
			{
				profile = (ModProfile)profiles.SelectedItem;
				await RefreshMods(capture: false);
			}
		};
		profiles.BackColor = Color.FromArgb(32, 39, 43);
		profiles.ForeColor = ForeColor;
		profiles.FlatStyle = FlatStyle.Flat;
		profiles.DisplayMember = "Name";
		ModProfile[] array = Mods.Profiles(settings);
		foreach (ModProfile item in array)
		{
			profiles.Items.Add(item);
		}
		if (profiles.Items.Count > 0)
		{
			profiles.SelectedIndex = 0;
			profile = (ModProfile)profiles.SelectedItem;
		}
		string path = Path.Combine(settings, "selected-profile.json");
		if (File.Exists(path))
		{
			try
			{
				string text = J.S(J.Parse(File.ReadAllText(path)), "name");
				foreach (ModProfile item2 in profiles.Items)
				{
					if (item2.Name == text)
					{
						profiles.SelectedItem = item2;
						profile = item2;
						break;
					}
				}
			}
			catch (Exception)
			{
			}
		}
		FormClosing += (object s, FormClosingEventArgs e) =>
		{
			if (busy)
			{
				e.Cancel = true;
				MessageBox.Show(this, "Close the running game or wait for the current operation to finish. The launcher restores your original mod script afterward.", Text);
			}
		};
		if (!preview)
		{
			Shown += async (object s, EventArgs e) =>
			{
				try
				{
					Directory.CreateDirectory(sessionRoot);
					using (new FileStream(Path.Combine(sessionRoot, "session.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None, 1, FileOptions.DeleteOnClose))
					{
						new ModScriptSession(sessionRoot, Mods.UserScript).Recover();
					}
				}
				catch (Exception ex2)
				{
					Error(ex2);
				}
				await RefreshMods(capture: false);
			};
			return;
		}
		packs = new List<ModPack>
		{
			new ModPack
			{
				Name = "Campaign overhaul.pack",
				Path = "campaign.pack",
				Source = "Workshop 123456",
				Enabled = true
			},
			new ModPack
			{
				Name = "Compatibility patch.pack",
				Path = "compat.pack",
				Source = "Remastered CE mods",
				Enabled = true,
				Dependencies = new string[1] { "Campaign overhaul.pack" }
			},
			new ModPack
			{
				Name = "Custom units.pack",
				Path = "units.pack",
				Source = "Game data"
			}
		};
		Render();
		status.Text = "Ready - Remastered CE 0.1.55-preview";
	}

	private void Add(FlowLayoutPanel panel, string text, Action action)
	{
		Button button = new Button
		{
			Text = text,
			AutoSize = true,
			Height = 32,
			FlatStyle = FlatStyle.Flat,
			BackColor = Color.FromArgb(40, 48, 53),
			ForeColor = ForeColor,
			Margin = new Padding(0, 0, 8, 0)
		};
		button.Click += (object s, EventArgs e) =>
		{
			try
			{
				action();
			}
			catch (Exception ex)
			{
				Error(ex);
			}
		};
		button.FlatAppearance.BorderColor = Color.FromArgb(72, 85, 91);
		panel.Controls.Add(button);
		actions.Add(button);
	}

	private void Error(Exception ex)
	{
		Engine.LogLauncherError(ex);
		status.Text = ex.Message;
		MessageBox.Show(this, ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
	}

	private void CaptureState()
	{
		profile.UseExistingScript = existingScript.Checked;
		profile.Name = profiles.Text.Trim();
		profile.Order = packs.Select((ModPack p) => p.Path).ToArray();
		profile.Enabled = (from p in packs
			where p.Enabled && !p.AutoLoaded
			select p.Path).ToArray();
	}

	private void Save()
	{
		CaptureState();
		Mods.SaveProfile(settings, profile, packs);
		profiles.Items.Clear();
		ModProfile[] array = Mods.Profiles(settings);
		foreach (ModProfile item in array)
		{
			profiles.Items.Add(item);
		}
		foreach (ModProfile item2 in profiles.Items)
		{
			if (item2.Name == profile.Name)
			{
				profiles.SelectedItem = item2;
				profile = item2;
				break;
			}
		}
		status.Text = "Saved profile: " + profile.Name;
	}

	private void SetBusy(bool value)
	{
		busy = value;
		grid.Enabled = !value && !existingScript.Checked;
		foreach (Control action in actions)
		{
			action.Enabled = !value;
		}
		play.Enabled = !value;
		play.Text = value ? "Please waitâ€¦" : (existingScript.Checked ? "Play existing script" : "Play Remastered CE");
		if (BusyChanged != null)
		{
			BusyChanged(value);
		}
	}

	private async Task RefreshMods(bool capture = true)
	{
		if (busy)
		{
			return;
		}
		if (capture)
		{
			CaptureState();
		}
		SetBusy(value: true);
		status.Text = "Finding local and Workshop packsâ€¦";
		try
		{
			List<ModPack> list = await Task.Run(() => Mods.Discover(game, profile.Folders));
			Mods.ApplyProfile(list, profile);
			existingScript.Checked = profile.UseExistingScript;
			packs = list;
			Render();
			status.Text = "Found " + packs.Count + " packs. Steam and Workshop files were read only.";
		}
		catch (Exception ex)
		{
			Error(ex);
		}
		finally
		{
			SetBusy(value: false);
		}
	}

	private void Render()
	{
		rendering = true;
		grid.Rows.Clear();
		int num = 1;
		foreach (ModPack pack in packs)
		{
			string text = pack.Error ?? (pack.AutoLoaded ? "Movie pack: always loaded from game data; move it to RemasteredCE/mods to manage it here." : ((pack.Dependencies.Length != 0) ? ("Requires: " + string.Join(", ", pack.Dependencies)) : "Ready"));
			int index = grid.Rows.Add(pack.Enabled, num++, pack.Name, pack.Source, text);
			grid.Rows[index].Tag = pack;
			grid.Rows[index].Cells[0].ReadOnly = pack.AutoLoaded;
			grid.Rows[index].Cells[2].ToolTipText = pack.Path;
		}
		rendering = false;
		UpdateSummary();
	}

	private void UpdateSummary()
	{
		List<string> list = Mods.Issues(packs, game);
		summary.Text = ((list.Count > 0) ? string.Join("  ", list.Take(2)) : (Enumerable.Count(packs, (ModPack p) => p.Enabled) + " enabled Â· " + Mods.OverlapSummary(packs)));
	}

	private void MoveSelection(int direction)
	{
		if (grid.SelectedRows.Count != 0)
		{
			int index = grid.SelectedRows[0].Index;
			int num = index + direction;
			if (num >= 0 && num < packs.Count)
			{
				ModPack item = packs[index];
				packs.RemoveAt(index);
				packs.Insert(num, item);
				Render();
				grid.ClearSelection();
				grid.Rows[num].Selected = true;
			}
		}
	}

	private void OpenMods()
	{
		string text = Path.Combine(game, "RemasteredCE", "mods");
		Directory.CreateDirectory(text);
		Process.Start(new ProcessStartInfo(text)
		{
			UseShellExecute = true
		});
	}

	private async Task CopyManifest()
	{
		SetBusy(value: true);
		try
		{
			string[] value = await Task.Run(() => packs.Where((ModPack p) => p.Enabled).Select((ModPack p, int i) => i + 1 + "\t" + p.Name + "\t" + Mods.Hash(p.Path)).ToArray());
			Clipboard.SetText("Remastered CE " + Engine.InstalledVersion(game) + "\r\nOrder\tPack\tSHA256\r\n" + string.Join("\r\n", value));
			status.Text = "Copied enabled mods, priority order and SHA256 hashes.";
		}
		catch (Exception ex)
		{
			Error(ex);
		}
		finally
		{
			SetBusy(value: false);
		}
	}

	private async Task Play()
	{
		bool manual = existingScript.Checked;
		List<string> list = manual ? new List<string>() : Mods.Issues(packs, game);
		if (list.Count > 0)
		{
			Error(new InvalidDataException(string.Join("\r\n", list)));
			return;
		}
		if (Mods.GameRunning())
		{
			Error(new IOException("Shogun 2 is already running."));
			return;
		}
		SetBusy(value: true);
		try
		{
			Save();
			Directory.CreateDirectory(settings);
			Directory.CreateDirectory(sessionRoot);
			using (new FileStream(Path.Combine(sessionRoot, "session.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None, 1, FileOptions.DeleteOnClose))
			{
				string active = manual ? null : await Task.Run(() => Mods.Stage(packs, settings, (string text) =>
				{
					BeginInvoke((Action)(() =>
					{
						status.Text = text;
					}));
				}));
				using ModScriptSession session = ModScriptSession.Prepare(sessionRoot, Mods.UserScript, active, packs, manual);
				status.Text = manual ? "Playing with your existing script. Launcher selections are ignored; the script is unchanged." : "Playing. Your original Steam mod script will be restored when the game closes.";
				string launcher = Path.Combine(game, "Launch_Remastered_CE.exe");
				IEnumerable<string> args = new string[2] { "--direct", "--wait" }.Concat(forwarded).Select(Mods.QuoteArgument);
				int num = await Task.Run(() =>
				{
					using Process process = Process.Start(new ProcessStartInfo(launcher, string.Join(" ", args))
					{
						WorkingDirectory = game,
						UseShellExecute = false,
						CreateNoWindow = true
					});
					process.WaitForExit();
					return process.ExitCode;
				});
				if (num != 0)
				{
					throw new IOException("The game launcher stopped with code " + num + ".");
				}
			}
			status.Text = manual ? "Game closed. Existing user script was left unchanged." : "Game closed. Original Steam mod script restored.";
		}
		catch (Exception ex)
		{
			Error(ex);
		}
		finally
		{
			SetBusy(value: false);
		}
	}
}
