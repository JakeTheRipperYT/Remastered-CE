using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

namespace RemasteredCE;

public sealed class MainForm : Form
{
	private readonly TextBox ce = new TextBox();

	private readonly TextBox legacy = new TextBox();

	private readonly TextBox package = new TextBox();

	private readonly TextBox log = new TextBox();

	private readonly Button install = new Button();

	private readonly Button launch = new Button();

	private readonly Button choosePackage = new Button();

	private readonly Button cancel = new Button();

	private readonly Button uninstall = new Button();

	private readonly Button github = new Button();

	private readonly ProgressBar progress = new ProgressBar();

	private readonly Label state = new Label();

	private CancellationTokenSource cancellation;

	private readonly string settings = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemasteredCE", "installer-settings.json");

	private bool busyState;

	private bool compactMode;

	private readonly List<Control> compactBrowsers = new List<Control>();

	private bool busy
	{
		get
		{
			return busyState;
		}
		set
		{
			busyState = value;
			if (BusyChanged != null)
			{
				BusyChanged(value);
			}
		}
	}

	public bool IsBusy => busy;

	public string GameDirectory => ce.Text.Trim();

	public event Action<bool> BusyChanged;

	public event Action BeforeMutation;

	public event Action<string> GameDirectoryChanged;

	public event Action<string> ModsRequested;

	public event Action<string, bool> InstallationChanged;

	public MainForm(bool preview = false, string game = null)
	{
		Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
		Text = "Remastered CE";
		ClientSize = new Size(810, 650);
		MinimumSize = new Size(820, 690);
		StartPosition = FormStartPosition.CenterScreen;
		Font = new Font("Segoe UI", 10f);
		BackColor = Color.FromArgb(23, 27, 30);
		ForeColor = Color.FromArgb(235, 239, 240);
		AutoScaleMode = AutoScaleMode.Dpi;
		Label value = new Label
		{
			Text = "REMASTERED CE",
			Font = new Font("Segoe UI Semibold", 23f),
			AutoSize = true,
			Location = new Point(28, 24)
		};
		Controls.Add(value);
		Controls.Add(new Label
		{
			Text = "By JakeTheRipper · Preview 0.1.17",
			AutoSize = true,
			ForeColor = Color.FromArgb(158, 176, 181),
			Location = new Point(31, 73)
		});
		FolderRow("Complete Edition installation", ce, 122);
		FolderRow("Original Shogun 2 installation", legacy, 204);
		Controls.Add(new Label
		{
			Text = "Release package",
			AutoSize = true,
			Location = new Point(30, 286)
		});
		StyleBox(package);
		package.Location = new Point(30, 312);
		package.Size = new Size(505, 29);
		package.ReadOnly = true;
		package.Text = "GitHub — latest release";
		Controls.Add(package);
		ButtonStyle(github, "GitHub", new Rectangle(547, 310, 108, 33));
		github.Click += (object s, EventArgs e) =>
		{
			package.Tag = null;
			package.Text = "GitHub — latest release";
		};
		ButtonStyle(choosePackage, "Offline…", new Rectangle(667, 310, 113, 33));
		ContextMenuStrip localMenu = new ContextMenuStrip();
		localMenu.Items.Add("Choose a downloaded .rce file…", null, (object s, EventArgs e) =>
		{
			using OpenFileDialog openFileDialog = new OpenFileDialog
			{
				Filter = "Remastered CE release (*.rce)|*.rce",
				Title = "Choose a signed Remastered CE update"
			};
			if (openFileDialog.ShowDialog() == DialogResult.OK)
			{
				try
				{
					using Release release2 = Release.Load(openFileDialog.FileName);
					package.Tag = openFileDialog.FileName;
					package.Text = Path.GetFileName(openFileDialog.FileName);
					Append("Selected " + J.S(release2.Manifest, "version") + "; signature verified.");
					return;
				}
				catch (Exception ex2)
				{
					ShowError(ex2);
					return;
				}
			}
		});
		localMenu.Items.Add("Use included release (offline)", null, (object s, EventArgs e) =>
		{
			package.Tag = ":embedded";
			package.Text = "Included release (offline)";
		});
		choosePackage.Click += (object s, EventArgs e) =>
		{
			localMenu.Show(choosePackage, new Point(0, choosePackage.Height));
		};
		ButtonStyle(install, "Install / Update Remastered CE", new Rectangle(30, 367, 325, 47));
		install.BackColor = Color.FromArgb(49, 117, 98);
		install.Click += async (object s, EventArgs e) =>
		{
			await Install();
		};
		ButtonStyle(launch, "Launch Remastered CE", new Rectangle(369, 367, 260, 47));
		launch.Click += (object s, EventArgs e) =>
		{
			if (ModsRequested != null)
			{
				ModsRequested(ce.Text.Trim());
			}
		};
		ButtonStyle(cancel, "Cancel", new Rectangle(643, 367, 137, 47));
		cancel.Enabled = false;
		cancel.Click += (object s, EventArgs e) =>
		{
			if (cancellation != null)
			{
				cancellation.Cancel();
			}
		};
		state.Text = "Vanilla game files stay untouched. Both games must be installed.";
		state.AutoSize = false;
		state.Location = new Point(30, 429);
		state.Size = new Size(520, 42);
		state.ForeColor = Color.FromArgb(158, 176, 181);
		Controls.Add(state);
		ButtonStyle(uninstall, "Uninstall Remastered CE", new Rectangle(562, 429, 218, 36));
		uninstall.Click += async (object s, EventArgs e) =>
		{
			await Uninstall();
		};
		progress.Location = new Point(30, 478);
		progress.Size = new Size(750, 9);
		Controls.Add(progress);
		StyleBox(log);
		log.Multiline = true;
		log.ReadOnly = true;
		log.ScrollBars = ScrollBars.Vertical;
		log.Location = new Point(30, 503);
		log.Size = new Size(750, 115);
		log.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
		Controls.Add(log);
		ce.Text = FindGame("Shogun 2 Complete Edition", "shogun2_complete_edition.exe");
		legacy.Text = FindGame("Total War SHOGUN 2", "Shogun2.exe");
		LoadSettings();
		if (preview)
		{
			ce.Text = "C:\\Users\\JakeTheRipper\\Games\\Shogun 2 Complete Edition";
			legacy.Text = "C:\\Users\\JakeTheRipper\\Games\\Total War SHOGUN 2";
		}
		if (!string.IsNullOrWhiteSpace(game))
		{
			ce.Text = game;
		}
		ce.TextChanged += (object s, EventArgs e) =>
		{
			if (GameDirectoryChanged != null)
			{
				GameDirectoryChanged(ce.Text.Trim());
			}
		};
		if (!preview)
		{
			try
			{
				using Release release = IncludedRelease();
				Append("Included release " + J.S(release.Manifest, "version") + ". Source assets are extracted locally; no complete game files are included.");
			}
			catch (Exception ex)
			{
				Append("Offline package unavailable: " + ex.Message + " Use GitHub or a downloaded signed release to repair.");
			}
		}
		FormClosing += (object s, FormClosingEventArgs e) =>
		{
			if (busy)
			{
				e.Cancel = true;
				MessageBox.Show(this, "Wait for the current operation to finish before closing.", Text, MessageBoxButtons.OK, MessageBoxIcon.Asterisk);
			}
		};
	}

	private void FolderRow(string label, TextBox box, int y)
	{
		Controls.Add(new Label
		{
			Text = label,
			AutoSize = true,
			Location = new Point(30, y)
		});
		StyleBox(box);
		box.Location = new Point(30, y + 27);
		box.Size = new Size(625, 29);
		Controls.Add(box);
		Button button = new Button();
		ButtonStyle(button, "Browse…", new Rectangle(667, y + 25, 113, 33));
		button.Click += (object s, EventArgs e) =>
		{
			using FolderBrowserDialog folderBrowserDialog = new FolderBrowserDialog
			{
				Description = label,
				SelectedPath = (Directory.Exists(box.Text) ? box.Text : "")
			};
			if (folderBrowserDialog.ShowDialog() == DialogResult.OK)
			{
				box.Text = folderBrowserDialog.SelectedPath;
			}
		};
	}

	private void ButtonStyle(Button b, string text, Rectangle bounds)
	{
		b.Text = text;
		b.Bounds = bounds;
		b.FlatStyle = FlatStyle.Flat;
		b.FlatAppearance.BorderColor = Color.FromArgb(72, 85, 91);
		b.BackColor = Color.FromArgb(40, 48, 53);
		b.ForeColor = ForeColor;
		Controls.Add(b);
	}

	private void StyleBox(TextBox t)
	{
		t.BackColor = Color.FromArgb(32, 39, 43);
		t.ForeColor = ForeColor;
		t.BorderStyle = BorderStyle.FixedSingle;
	}

	private void Append(string s)
	{
		log.AppendText(DateTime.Now.ToString("HH:mm:ss") + "  " + s + Environment.NewLine);
	}

	private void ShowError(Exception ex)
	{
		Engine.LogLauncherError(ex);
		string s = ((ex is UnauthorizedAccessException) ? "Windows denied access to the selected folder. Close the game and, if this folder requires it, run this installer as administrator." : ex.Message);
		Append(s);
		MessageBox.Show(this, s, Text, MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
	}

	private async Task Install()
	{
		if (busy)
		{
			return;
		}
		string cePath = ce.Text.Trim();
		string legacyPath = legacy.Text.Trim();
		string text = package.Tag as string;
		if (!Directory.Exists(cePath) || !Directory.Exists(legacyPath))
		{
			ShowError(new IOException("Choose both installed game folders first."));
			return;
		}
		busy = true;
		uninstall.Enabled = false;
		install.Enabled = false;
		launch.Enabled = false;
		choosePackage.Enabled = false;
		github.Enabled = false;
		ce.ReadOnly = true;
		legacy.ReadOnly = true;
		cancel.Enabled = true;
		cancellation = new CancellationTokenSource();
		progress.Value = 0;
		try
		{
			if (BeforeMutation != null)
			{
				BeforeMutation();
			}
			SaveSettings();
			if (text == null)
			{
				state.Text = "Checking GitHub for the latest Remastered CE release...";
				Append(state.Text);
				OnlineRelease latest = await Task.Run(() => OnlineUpdates.Latest(cancellation.Token));
				Append("Latest published release: " + latest.Version);
				string path = Engine.Under(cePath, "RemasteredCE/install-state.json");
				if (File.Exists(path))
				{
					string text2 = J.S(J.Parse(File.ReadAllText(path)), "version");
					if (!OnlineUpdates.NeedsUpdate(text2, latest.Version))
					{
						if (InstallerLauncher.NeedsUpdate(cePath, text2, latest.Version))
						{
							await Task.Run(() => InstallerLauncher.Repair(cePath));
							state.Text = "Launcher updated to 0.1.25 mod fix 2";
							Append("The corrected launcher is installed. Game packs and mods were kept.");
							return;
						}
						state.Text = "Up to date · " + text2;
						Append("No newer release is available. Your installed files were kept.");
						return;
					}
				}
				state.Text = "Downloading Remastered CE " + latest.Version + "...";
				Progress<Tuple<long, long>> downloadProgress = new Progress<Tuple<long, long>>((Tuple<long, long> v) =>
				{
					state.Text = "Downloading " + latest.Version + " · " + v.Item1 / 1024 + " KB";
					progress.Value = (int)((v.Item2 > 0) ? Math.Min(100L, v.Item1 * 100 / v.Item2) : 0);
				});
				string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RemasteredCE", "downloads");
				text = await Task.Run(() => OnlineUpdates.Download(latest, folder, cancellation.Token, (long a, long b) =>
				{
					((IProgress<Tuple<long, long>>)downloadProgress).Report(Tuple.Create(a, b));
				}));
				Append("Downloaded " + latest.Version + "; release signature verified.");
				progress.Value = 0;
			}
			else if (text == ":embedded")
			{
				text = null;
			}
			Release release = (string.IsNullOrEmpty(text) ? IncludedRelease() : Release.Load(text));
			try
			{
				Append("Starting " + J.S(release.Manifest, "version") + ". Existing Remastered files will be retained as a previous version.");
				Progress<Tuple<string, int>> uiProgress = new Progress<Tuple<string, int>>((Tuple<string, int> v) =>
				{
					state.Text = v.Item1;
					progress.Value = Math.Max(0, Math.Min(100, v.Item2));
					Append(v.Item1);
				});
				Engine engine = new Engine
				{
					Cancel = cancellation.Token,
					Progress = (string s, int p) =>
					{
						((IProgress<Tuple<string, int>>)uiProgress).Report(Tuple.Create(s, p));
					}
				};
				await Task.Run(() =>
				{
					engine.Install(release, cePath, legacyPath);
				});
				state.Text = "Ready · " + J.S(release.Manifest, "version");
				Append("Installation complete. Launch Remastered CE when ready.");
				if (InstallationChanged != null)
				{
					InstallationChanged(cePath, arg2: true);
				}
			}
			finally
			{
				if (release != null)
				{
					((IDisposable)release).Dispose();
				}
			}
		}
		catch (OperationCanceledException)
		{
			state.Text = "Cancelled. Installed files were preserved.";
			Append(state.Text);
		}
		catch (Exception ex2)
		{
			state.Text = "Installation stopped. See the message below.";
			ShowError(ex2);
		}
		finally
		{
			busy = false;
			uninstall.Enabled = true;
			install.Enabled = true;
			launch.Enabled = true;
			choosePackage.Enabled = true;
			github.Enabled = true;
			TextBox textBox = ce;
			bool readOnly = (legacy.ReadOnly = compactMode);
			textBox.ReadOnly = readOnly;
			cancel.Enabled = false;
			cancellation.Dispose();
			cancellation = null;
		}
	}

	private async Task Uninstall()
	{
		if (busy)
		{
			return;
		}
		string cePath = ce.Text.Trim();
		if (!Directory.Exists(cePath))
		{
			ShowError(new IOException("Choose the Complete Edition game folder first."));
		}
		else
		{
			if (MessageBox.Show(this, "Remove the active Remastered CE installation and its launchers?\n\nVanilla game files, saves, settings, and previous-version backup folders will be kept.", "Uninstall Remastered CE", MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button2) != DialogResult.Yes)
			{
				return;
			}
			busy = true;
			install.Enabled = false;
			launch.Enabled = false;
			uninstall.Enabled = false;
			choosePackage.Enabled = false;
			github.Enabled = false;
			ce.ReadOnly = true;
			legacy.ReadOnly = true;
			cancel.Enabled = false;
			progress.Value = 0;
			try
			{
				if (BeforeMutation != null)
				{
					BeforeMutation();
				}
				Progress<Tuple<string, int>> uiProgress = new Progress<Tuple<string, int>>((Tuple<string, int> v) =>
				{
					state.Text = v.Item1;
					progress.Value = v.Item2;
					Append(v.Item1);
				});
				Engine engine = new Engine
				{
					Progress = (string s, int p) =>
					{
						((IProgress<Tuple<string, int>>)uiProgress).Report(Tuple.Create(s, p));
					}
				};
				await Task.Run(() =>
				{
					engine.Uninstall(cePath);
				});
				if (InstallationChanged != null)
				{
					InstallationChanged(cePath, arg2: true);
				}
				Append("Use Steam to launch the vanilla game.");
			}
			catch (Exception ex)
			{
				state.Text = "Uninstall stopped. See the message below.";
				ShowError(ex);
			}
			finally
			{
				busy = false;
				install.Enabled = true;
				launch.Enabled = true;
				uninstall.Enabled = true;
				choosePackage.Enabled = true;
				github.Enabled = true;
				TextBox textBox = ce;
				bool readOnly = (legacy.ReadOnly = compactMode);
				textBox.ReadOnly = readOnly;
			}
		}
	}

	private void LoadSettings()
	{
		try
		{
			if (File.Exists(settings))
			{
				Dictionary<string, object> d = J.Parse(File.ReadAllText(settings));
				if (Directory.Exists(J.S(d, "ce")))
				{
					ce.Text = J.S(d, "ce");
				}
				if (Directory.Exists(J.S(d, "legacy")))
				{
					legacy.Text = J.S(d, "legacy");
				}
			}
		}
		catch
		{
		}
	}

	private void SaveSettings()
	{
		Directory.CreateDirectory(Path.GetDirectoryName(settings));
		File.WriteAllText(settings, J.Json().Serialize(new Dictionary<string, object>
		{
			{
				"ce",
				ce.Text.Trim()
			},
			{
				"legacy",
				legacy.Text.Trim()
			}
		}));
	}

	private static string FindGame(string folder, string exe)
	{
		List<string> list = new List<string>();
		try
		{
			using RegistryKey registryKey = Registry.CurrentUser.OpenSubKey("Software\\Valve\\Steam");
			if (registryKey != null)
			{
				string text = Convert.ToString(registryKey.GetValue("SteamPath"));
				if (!string.IsNullOrEmpty(text))
				{
					list.Add(text);
				}
			}
		}
		catch
		{
		}
		list.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Steam"));
		DriveInfo[] drives = DriveInfo.GetDrives();
		foreach (DriveInfo driveInfo in drives)
		{
			if (driveInfo.DriveType == DriveType.Fixed)
			{
				list.Add(Path.Combine(driveInfo.RootDirectory.FullName, "SteamLibrary"));
			}
		}
		string[] array = list.ToArray();
		for (int i = 0; i < array.Length; i++)
		{
			string path = Path.Combine(array[i], "steamapps", "libraryfolders.vdf");
			try
			{
				if (!File.Exists(path))
				{
					continue;
				}
				foreach (Match item in Regex.Matches(File.ReadAllText(path), "\"path\"\\s+\"([^\"]+)\""))
				{
					list.Add(item.Groups[1].Value.Replace("\\\\", "\\"));
				}
			}
			catch
			{
			}
		}
		foreach (string item2 in list.Distinct(StringComparer.OrdinalIgnoreCase))
		{
			string text2 = Path.Combine(item2, "steamapps", "common", folder);
			if (File.Exists(Path.Combine(text2, exe)))
			{
				return text2;
			}
		}
		return "";
	}

	public void SetGameDirectory(string path)
	{
		ce.Text = path ?? "";
	}

	public static string FindGame()
	{
		return FindGame("Shogun 2 Complete Edition", "shogun2_complete_edition.exe");
	}

	private Release IncludedRelease()
	{
		if (Assembly.GetExecutingAssembly().GetManifestResourceNames().Contains("release"))
		{
			return Release.Load(null);
		}
		string path = Path.Combine(ce.Text.Trim(), "RemasteredCE", "release.rce");
		if (!File.Exists(path))
		{
			throw new FileNotFoundException("The installed offline release is missing. Open the downloaded Remastered CE setup to repair it.");
		}
		return Release.Load(path);
	}

	public void ConfigureCompact()
	{
		compactMode = true;
		HashSet<Control> hashSet = new HashSet<Control>
		{
			ce, legacy, package, log, install, launch, cancel, uninstall, choosePackage, github,
			state, progress
		};
		Control[] array = Controls.Cast<Control>().ToArray();
		Controls.Clear();
		Control[] array2 = array;
		foreach (Control control in array2)
		{
			if (!hashSet.Contains(control))
			{
				control.Dispose();
			}
		}
		TableLayoutPanel grid = new TableLayoutPanel
		{
			Dock = DockStyle.Fill,
			Padding = new Padding(12),
			ColumnCount = 1,
			RowCount = 14
		};
		grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
		int[] array3 = new int[14]
		{
			22, 38, 22, 38, 22, 34, 38, 48, 42, 38,
			58, 12, 0, 0
		};
		for (int j = 0; j < array3.Length; j++)
		{
			grid.RowStyles.Add(new RowStyle((j != 12) ? SizeType.Absolute : SizeType.Percent, (j == 12) ? 100 : array3[j]));
		}
		Controls.Add(grid);
		Action<Control, int> action = (Control c, int r) =>
		{
			c.Dock = DockStyle.Fill;
			c.Margin = new Padding(0, 3, 0, 3);
			c.AutoSize = false;
			grid.Controls.Add(c, 0, r);
		};
		action(new Label
		{
			Text = "Complete Edition installation",
			TextAlign = ContentAlignment.MiddleLeft
		}, 0);
		action(FolderPicker(ce, "Choose the Complete Edition game folder"), 1);
		action(new Label
		{
			Text = "Original Shogun 2 installation",
			TextAlign = ContentAlignment.MiddleLeft
		}, 2);
		action(FolderPicker(legacy, "Choose the original Shogun 2 game folder"), 3);
		action(new Label
		{
			Text = "Signed release package",
			TextAlign = ContentAlignment.MiddleLeft
		}, 4);
		action(package, 5);
		TableLayoutPanel tableLayoutPanel = new TableLayoutPanel
		{
			ColumnCount = 2
		};
		tableLayoutPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));
		tableLayoutPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50f));
		Button[] array4 = new Button[2] { github, choosePackage };
		foreach (Button button in array4)
		{
			button.Dock = DockStyle.Fill;
			tableLayoutPanel.Controls.Add(button);
		}
		action(tableLayoutPanel, 6);
		action(install, 7);
		launch.Visible = false;
		action(uninstall, 8);
		action(cancel, 9);
		action(state, 10);
		action(progress, 11);
		action(log, 12);
		log.Multiline = true;
		log.ScrollBars = ScrollBars.Vertical;
		TextBox textBox = ce;
		bool readOnly = (legacy.ReadOnly = true);
		textBox.ReadOnly = readOnly;
		BusyChanged += (bool value) =>
		{
			foreach (Control compactBrowser in compactBrowsers)
			{
				compactBrowser.Enabled = !value;
			}
			TextBox textBox2 = ce;
			bool readOnly2 = (legacy.ReadOnly = true);
			textBox2.ReadOnly = readOnly2;
		};
	}

	private Control FolderPicker(TextBox box, string title)
	{
		TableLayoutPanel tableLayoutPanel = new TableLayoutPanel
		{
			ColumnCount = 2,
			ColumnStyles = 
			{
				new ColumnStyle(SizeType.Percent, 100f),
				new ColumnStyle(SizeType.Absolute, 88f)
			}
		};
		box.Dock = DockStyle.Fill;
		box.ReadOnly = true;
		tableLayoutPanel.Controls.Add(box, 0, 0);
		Button button = new Button
		{
			Text = "Browse…",
			Dock = DockStyle.Fill,
			FlatStyle = FlatStyle.Flat,
			BackColor = Color.FromArgb(40, 48, 53)
		};
		tableLayoutPanel.Controls.Add(button, 1, 0);
		compactBrowsers.Add(button);
		button.Click += (object s, EventArgs e) =>
		{
			using FolderBrowserDialog folderBrowserDialog = new FolderBrowserDialog
			{
				Description = title,
				SelectedPath = (Directory.Exists(box.Text) ? box.Text : "")
			};
			if (folderBrowserDialog.ShowDialog() == DialogResult.OK)
			{
				box.Text = folderBrowserDialog.SelectedPath;
			}
		};
		return tableLayoutPanel;
	}
}
