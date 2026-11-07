using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace RemasteredCE;

public sealed class UnifiedForm : Form
{
	public readonly SplitContainer Body = new SplitContainer();

	private readonly bool preview;

	private readonly bool? installedOverride;

	private readonly string[] forwarded;

	private readonly Label notice = new Label();

	private string modsGame;

	private bool changing;

	public MainForm SetupPanel { get; private set; }

	public ModForm ModsPanel { get; private set; }

	public bool Busy
	{
		get
		{
			if (!SetupPanel.IsBusy)
			{
				if (ModsPanel != null)
				{
					return ModsPanel.IsBusy;
				}
				return false;
			}
			return true;
		}
	}

	public event Action<Exception> ErrorOccurred;

	public UnifiedForm(string game, string[] arguments = null, bool previewMode = false, bool? assumeInstalled = null)
	{
		preview = previewMode;
		installedOverride = (preview ? assumeInstalled : ((bool?)null));
		forwarded = arguments ?? new string[0];
		Text = "Remastered CE";
		Font = new Font("Segoe UI", 10f);
		BackColor = Color.FromArgb(23, 27, 30);
		ForeColor = Color.FromArgb(235, 239, 240);
		AutoScaleMode = AutoScaleMode.Dpi;
		Rectangle workingArea = Screen.PrimaryScreen.WorkingArea;
		ClientSize = new Size(Math.Min(1720, workingArea.Width - 70), Math.Min(970, workingArea.Height - 80));
		MinimumSize = new Size(1280, 800);
		StartPosition = FormStartPosition.CenterScreen;
		TableLayoutPanel tableLayoutPanel = new TableLayoutPanel
		{
			Dock = DockStyle.Fill,
			ColumnCount = 1,
			RowCount = 2,
			Padding = new Padding(18, 12, 18, 18)
		};
		tableLayoutPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Absolute, 84f));
		tableLayoutPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));
		Controls.Add(tableLayoutPanel);
		TableLayoutPanel tableLayoutPanel2 = new TableLayoutPanel
		{
			Dock = DockStyle.Fill,
			ColumnCount = 2,
			RowCount = 2
		};
		tableLayoutPanel2.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100f));
		tableLayoutPanel2.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 150f));
		tableLayoutPanel2.RowStyles.Add(new RowStyle(SizeType.Absolute, 48f));
		tableLayoutPanel2.RowStyles.Add(new RowStyle(SizeType.Percent, 100f));
		tableLayoutPanel2.Controls.Add(new Label
		{
			Text = "REMASTERED CE",
			Font = new Font("Segoe UI Semibold", 26f),
			Dock = DockStyle.Fill,
			TextAlign = ContentAlignment.MiddleLeft
		}, 0, 0);
		tableLayoutPanel2.Controls.Add(new Label
		{
			Text = "Install, update and manage your mods in one place.",
			ForeColor = Color.FromArgb(158, 176, 181),
			Dock = DockStyle.Fill,
			TextAlign = ContentAlignment.TopLeft
		}, 0, 1);
		tableLayoutPanel2.Controls.Add(new Label
		{
			Text = "0.1.80 preview — mod loading fix included",
			Dock = DockStyle.Fill,
			TextAlign = ContentAlignment.MiddleRight,
			ForeColor = Color.FromArgb(158, 176, 181)
		}, 1, 0);
		tableLayoutPanel.Controls.Add(tableLayoutPanel2);
		Body.Dock = DockStyle.Fill;
		Body.Orientation = Orientation.Vertical;
		Body.FixedPanel = FixedPanel.Panel1;
		Body.SplitterWidth = 8;
		Body.BackColor = Color.FromArgb(72, 85, 91);
		Body.Size = new Size(Math.Max(1200, ClientSize.Width - 36), Math.Max(600, ClientSize.Height - 100));
		Body.Panel1MinSize = 410;
		Body.Panel2MinSize = 780;
		Body.SplitterDistance = 435;
		tableLayoutPanel.Controls.Add(Body);
		Body.Panel1.BackColor = (Body.Panel2.BackColor = BackColor);
		SetupPanel = new MainForm(preview, game);
		SetupPanel.ConfigureCompact();
		Embed(SetupPanel, Body.Panel1);
		notice.Text = "Choose your game folder and install the patch to enable mods and Play.";
		notice.Dock = DockStyle.Fill;
		notice.TextAlign = ContentAlignment.MiddleCenter;
		notice.ForeColor = ForeColor;
		Body.Panel2.Controls.Add(notice);
		SetupPanel.BeforeMutation += () =>
		{
			if (ModsPanel != null)
			{
				ModsPanel.SaveCurrentProfile();
			}
		};
		SetupPanel.BusyChanged += (bool value) =>
		{
			if (ModsPanel != null)
			{
				ModsPanel.Enabled = !value;
			}
		};
		SetupPanel.GameDirectoryChanged += (string path) =>
		{
			if (changing)
			{
				return;
			}
			try
			{
				ChangeDirectory(path, force: false);
			}
			catch (Exception ex)
			{
				ReportError(ex);
				if (modsGame != null)
				{
					changing = true;
					SetupPanel.SetGameDirectory(modsGame);
					changing = false;
				}
			}
		};
		SetupPanel.ModsRequested += (string path) =>
		{
			ChangeDirectory(path, force: false);
			if (ModsPanel != null)
			{
				ModsPanel.Focus();
			}
		};
		SetupPanel.InstallationChanged += (string path, bool success) =>
		{
			if (!success)
			{
				return;
			}
			try
			{
				ChangeDirectory(path, force: true);
			}
			catch (Exception ex)
			{
				ReportError(ex);
			}
		};
		ChangeDirectory(SetupPanel.GameDirectory, force: false);
		FormClosing += (object sender, FormClosingEventArgs e) =>
		{
			if (Busy)
			{
				e.Cancel = true;
				MessageBox.Show(this, "Wait for installation or preparation to finish, or close the running game. Your original mod script is restored after playing.", Text);
			}
		};
	}

	private void ReportError(Exception ex)
	{
		if (ErrorOccurred != null)
		{
			ErrorOccurred(ex);
			return;
		}
		Engine.LogLauncherError(ex);
		MessageBox.Show(this, ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
	}

	private bool Available(string path)
	{
		bool? flag = installedOverride;
		if (!flag.HasValue)
		{
			if (!string.IsNullOrWhiteSpace(path))
			{
				return File.Exists(Path.Combine(path, "RemasteredCE", "install-state.json"));
			}
			return false;
		}
		return flag == true;
	}

	private void ChangeDirectory(string path, bool force)
	{
		if (!force && ModsPanel != null && string.Equals(modsGame, Path.GetFullPath(path), StringComparison.OrdinalIgnoreCase))
		{
			return;
		}
		if (ModsPanel != null)
		{
			if (!force)
			{
				ModsPanel.SaveCurrentProfile();
			}
			Body.Panel2.Controls.Remove(ModsPanel);
			ModsPanel.Dispose();
			ModsPanel = null;
			modsGame = null;
		}
		notice.Visible = true;
		if (Available(path))
		{
			modsGame = Path.GetFullPath(path);
			ModsPanel = new ModForm(modsGame, forwarded, preview);
			ModsPanel.ConfigureCompact();
			ModsPanel.Enabled = !SetupPanel.IsBusy;
			ModsPanel.BusyChanged += (bool value) =>
			{
				SetupPanel.Enabled = !value;
			};
			notice.Visible = false;
			Embed(ModsPanel, Body.Panel2);
			ModsPanel.BringToFront();
		}
	}

	private static void Embed(Form form, Control parent)
	{
		form.TopLevel = false;
		form.FormBorderStyle = FormBorderStyle.None;
		form.MinimumSize = Size.Empty;
		form.ShowInTaskbar = false;
		form.Dock = DockStyle.Fill;
		parent.Controls.Add(form);
		form.Show();
	}
}
