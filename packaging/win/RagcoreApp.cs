using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace RAGcore
{
    internal static class Program
    {
        [STAThread]
        private static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }

    internal sealed class MainForm : Form
    {
        private const int Port = 8765;
        private const string Host = "127.0.0.1";
        private static readonly string Url = "http://" + Host + ":" + Port;
        private static readonly string HealthUrl = Url + "/health";

        private readonly string _bundleDir;
        private readonly string _dataDir;
        private readonly string _pythonExe;
        private readonly string _backendDir;
        private readonly string _logDir;
        private readonly Label _statusLabel;
        private readonly Label _urlLabel;
        private readonly Label _logLabel;
        private readonly Button _browserButton;
        private readonly Button _quitButton;
        private readonly System.Windows.Forms.Timer _pollTimer;

        private Process _serverProcess;
        private bool _ownsServer;
        private bool _closing;

        public MainForm()
        {
            _bundleDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            _dataDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "RAGcore");
            _pythonExe = Path.Combine(_bundleDir, "python", "python.exe");
            _backendDir = Path.Combine(_bundleDir, "backend");
            _logDir = Path.Combine(_dataDir, "logs");

            Text = "RAGcore";
            Font = new Font("Microsoft YaHei UI", 9F);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = true;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(460, 280);
            Icon = SystemIcons.Application;

            var title = new Label
            {
                Text = "RAGcore 笔记知识库",
                Font = new Font(Font.FontFamily, 14F, FontStyle.Bold),
                AutoSize = true,
                Location = new Point(20, 16)
            };

            _statusLabel = new Label
            {
                Text = "● 正在启动，请稍候…",
                Font = new Font(Font.FontFamily, 11F),
                AutoSize = true,
                Location = new Point(20, 56)
            };

            _urlLabel = new Label
            {
                Text = "访问地址：" + Url,
                ForeColor = Color.FromArgb(37, 99, 235),
                AutoSize = true,
                Location = new Point(20, 88)
            };

            var hint = new Label
            {
                Text = "关闭此窗口将停止后台服务（笔记数据已保存在用户目录）",
                ForeColor = Color.Gray,
                MaximumSize = new Size(420, 0),
                AutoSize = true,
                Location = new Point(20, 118)
            };

            _logLabel = new Label
            {
                Text = "日志：" + _logDir,
                ForeColor = Color.DimGray,
                MaximumSize = new Size(420, 0),
                AutoSize = true,
                Location = new Point(20, 158)
            };

            _browserButton = new Button
            {
                Text = "打开浏览器",
                Location = new Point(20, 220),
                Size = new Size(110, 32),
                Enabled = false
            };
            _browserButton.Click += (_, __) => OpenBrowser();

            _quitButton = new Button
            {
                Text = "退出并停止服务",
                Location = new Point(140, 220),
                Size = new Size(140, 32)
            };
            _quitButton.Click += (_, __) => Close();

            Controls.Add(title);
            Controls.Add(_statusLabel);
            Controls.Add(_urlLabel);
            Controls.Add(hint);
            Controls.Add(_logLabel);
            Controls.Add(_browserButton);
            Controls.Add(_quitButton);

            _pollTimer = new System.Windows.Forms.Timer { Interval = 1000 };
            _pollTimer.Tick += (_, __) => UpdateStatus();
            _pollTimer.Start();

            FormClosing += OnFormClosing;
            Shown += async (_, __) => await StartAsync();
        }

        private async Task StartAsync()
        {
            try
            {
                if (!File.Exists(_pythonExe))
                    throw new FileNotFoundException("未找到内置 Python", _pythonExe);
                if (!Directory.Exists(_backendDir))
                    throw new DirectoryNotFoundException("未找到后端目录: " + _backendDir);

                Directory.CreateDirectory(_logDir);

                if (IsServerUp())
                {
                    _statusLabel.Text = "● 服务运行中";
                    _browserButton.Enabled = true;
                    OpenBrowser();
                    return;
                }

                await Task.Run((Action)StartServer);

                var ready = await WaitForServerAsync(60);
                if (!ready)
                {
                    MessageBox.Show(
                        this,
                        "服务未在 60 秒内就绪。\n请查看日志：\n" + _logDir,
                        "RAGcore 启动失败",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);
                    StopServer();
                    Close();
                    return;
                }

                _statusLabel.Text = "● 服务运行中";
                _browserButton.Enabled = true;
                OpenBrowser();
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    this,
                    ex.Message,
                    "RAGcore 启动失败",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
                Close();
            }
        }

        private void StartServer()
        {
            var stdoutPath = Path.Combine(_logDir, "ragcore.out.log");
            var stderrPath = Path.Combine(_logDir, "ragcore.err.log");

            var psi = new ProcessStartInfo
            {
                FileName = _pythonExe,
                Arguments = "-m uvicorn server.main:app --host " + Host + " --port " + Port,
                WorkingDirectory = _backendDir,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            psi.EnvironmentVariables["RAGCORE_BUNDLE"] = "1";
            psi.EnvironmentVariables["RAGCORE_BUNDLE_DIR"] = _bundleDir;
            psi.EnvironmentVariables["RAGCORE_DATA_DIR"] = _dataDir;
            psi.EnvironmentVariables["SERVE_STATIC"] = "true";
            psi.EnvironmentVariables["PORT"] = Port.ToString();
            psi.EnvironmentVariables["PYTHONPATH"] = _backendDir;

            _serverProcess = new Process { StartInfo = psi, EnableRaisingEvents = true };
            _serverProcess.OutputDataReceived += (_, e) => AppendLog(stdoutPath, e.Data);
            _serverProcess.ErrorDataReceived += (_, e) => AppendLog(stderrPath, e.Data);
            _serverProcess.Start();
            _serverProcess.BeginOutputReadLine();
            _serverProcess.BeginErrorReadLine();
            _ownsServer = true;

            File.WriteAllText(Path.Combine(_dataDir, "ragcore.pid"), _serverProcess.Id.ToString());
        }

        private static void AppendLog(string path, string line)
        {
            if (string.IsNullOrEmpty(line)) return;
            try
            {
                File.AppendAllText(path, line + Environment.NewLine);
            }
            catch
            {
                // ignore logging failures
            }
        }

        private static bool IsServerUp()
        {
            try
            {
                var request = (HttpWebRequest)WebRequest.Create(HealthUrl);
                request.Timeout = 1000;
                request.Method = "GET";
                using (var response = (HttpWebResponse)request.GetResponse())
                {
                    return response.StatusCode == HttpStatusCode.OK;
                }
            }
            catch
            {
                return false;
            }
        }

        private static async Task<bool> WaitForServerAsync(int seconds)
        {
            var deadline = DateTime.UtcNow.AddSeconds(seconds);
            while (DateTime.UtcNow < deadline)
            {
                if (IsServerUp()) return true;
                await Task.Delay(250);
            }
            return false;
        }

        private void UpdateStatus()
        {
            if (_closing) return;

            if (IsServerUp())
            {
                _statusLabel.Text = "● 服务运行中";
                _browserButton.Enabled = true;
            }
            else if (_serverProcess != null && !_serverProcess.HasExited)
            {
                _statusLabel.Text = "● 正在启动，请稍候…";
            }
            else if (_ownsServer)
            {
                _statusLabel.Text = "● 服务未响应，请查看日志";
            }
        }

        private static void OpenBrowser()
        {
            try
            {
                Process.Start(new ProcessStartInfo(Url) { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                MessageBox.Show("无法打开浏览器：\n" + ex.Message, "RAGcore", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        private void OnFormClosing(object sender, FormClosingEventArgs e)
        {
            if (_closing) return;

            if (_ownsServer && _serverProcess != null && !_serverProcess.HasExited)
            {
                var result = MessageBox.Show(
                    this,
                    "确定退出并停止后台服务吗？",
                    "退出 RAGcore",
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Question);
                if (result != DialogResult.Yes)
                {
                    e.Cancel = true;
                    return;
                }
            }

            _closing = true;
            _pollTimer.Stop();
            StopServer();
        }

        private void StopServer()
        {
            if (_serverProcess == null) return;

            try
            {
                if (!_serverProcess.HasExited)
                {
                    _serverProcess.Kill();
                    _serverProcess.WaitForExit(3000);
                }
            }
            catch
            {
                // ignore
            }
            finally
            {
                _serverProcess.Dispose();
                _serverProcess = null;
            }

            try
            {
                var pidFile = Path.Combine(_dataDir, "ragcore.pid");
                if (File.Exists(pidFile)) File.Delete(pidFile);
            }
            catch
            {
                // ignore
            }
        }
    }
}
