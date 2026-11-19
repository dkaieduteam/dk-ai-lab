using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

// Diagnostic log for Tunnel startup. Every line is redacted before it reaches disk.
// Kept separate from TrainingOutput so an already-open console can load it without restart.
public sealed class TrainingDebugLog : IDisposable {
    private readonly object gate = new object();
    private readonly List<string> secrets = new List<string>();
    private StreamWriter writer;
    public readonly string Path;

    private static readonly Regex[] Patterns = new Regex[] {
        new Regex(@"sk-[A-Za-z0-9_\-]{6,}"),
        new Regex(@"eyJ[A-Za-z0-9_\-]{10,}(\.[A-Za-z0-9_\-]+)*"),
        new Regex(@"(?i)(bearer\s+)[^\s"",]+"),
        new Regex(@"(?i)((api[_-]?key|authorization|token|secret|password)[""']?\s*[:=]\s*[""']?)[^\s"",']+")
    };

    public TrainingDebugLog(string path) {
        Path = path;
        Directory.CreateDirectory(System.IO.Path.GetDirectoryName(path));
        writer = new StreamWriter(path, true, new UTF8Encoding(false));
        writer.AutoFlush = true;
    }

    // Registers a value that must never appear in the log as-is.
    public void AddSecret(string value) {
        if (string.IsNullOrEmpty(value)) return;
        lock (gate) { secrets.Add(value); }
    }

    public void Attach(Process process) {
        process.OutputDataReceived += delegate(object s, DataReceivedEventArgs a) { Write("OUT", a.Data); };
        process.ErrorDataReceived += delegate(object s, DataReceivedEventArgs a) { Write("ERR", a.Data); };
    }

    public void Write(string source, string line) {
        if (line == null) return;
        lock (gate) {
            if (writer == null) return;
            string text = Redact(line);
            try { writer.WriteLine("{0:yyyy-MM-dd HH:mm:ss.fff} [{1}] {2}", DateTime.Now, source, text); }
            catch (Exception) { }
        }
    }

    public string Redact(string line) {
        string text = line;
        foreach (string secret in secrets) {
            if (!string.IsNullOrEmpty(secret) && secret.Length >= 4) text = text.Replace(secret, Mask(secret));
        }
        text = Patterns[0].Replace(text, "sk-***");
        text = Patterns[1].Replace(text, "eyJ***");
        text = Patterns[2].Replace(text, "$1***");
        text = Patterns[3].Replace(text, "$1***");
        return text;
    }

    // Keeps only the shape needed to compare with the OpenAI Platform screen.
    public static string Mask(string value) {
        if (string.IsNullOrEmpty(value)) return "(empty)";
        if (value.StartsWith("tunnel_") && value.Length > 15)
            return value.Substring(0, 7) + "***" + value.Substring(value.Length - 4) + "(len " + value.Length + ")";
        return "***(len " + value.Length + ")";
    }

    public void Dispose() {
        lock (gate) {
            if (writer != null) { writer.Dispose(); writer = null; }
        }
    }
}
