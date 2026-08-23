using System;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

namespace AlnuaHub
{
    internal static class Program
    {
        private const string AppId = "ALNUA.Hub";

        [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
        private static extern int SetCurrentProcessExplicitAppUserModelID(string appID);

        [STAThread]
        private static void Main(string[] args)
        {
            try
            {
                SetCurrentProcessExplicitAppUserModelID(AppId);
            }
            catch
            {
                // Best-effort — the .exe icon still drives the taskbar.
            }

            string url = args.Length > 0 ? args[0] : "http://localhost:3000";
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new HubForm(url));
        }
    }

    internal sealed class HubForm : Form
    {
        private readonly string _url;
        private readonly WebView2 _web = new WebView2 { Dock = DockStyle.Fill };

        public HubForm(string url)
        {
            _url = url;
            Text = "ALNUA Hub";
            Width = 1440;
            Height = 900;
            MinimumSize = new Size(1024, 700);
            StartPosition = FormStartPosition.CenterScreen;
            BackColor = Color.FromArgb(14, 16, 20);

            string ico = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "alnua-hub.ico");
            if (File.Exists(ico))
            {
                Icon = new Icon(ico);
            }

            Controls.Add(_web);
            Shown += OnShown;
        }

        private async void OnShown(object sender, EventArgs e)
        {
            try
            {
                string userData = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                    "ALNUA",
                    "hub-webview");
                Directory.CreateDirectory(userData);
                CoreWebView2Environment env = await CoreWebView2Environment.CreateAsync(null, userData);
                await _web.EnsureCoreWebView2Async(env);
                _web.CoreWebView2.Settings.AreDefaultContextMenusEnabled = true;
                _web.CoreWebView2.Settings.AreDevToolsEnabled = true;
                _web.CoreWebView2.Navigate(_url);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    "Impossible d'ouvrir ALNUA Hub (WebView2)." + Environment.NewLine + ex.Message,
                    "ALNUA Hub",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
                Close();
            }
        }
    }
}
