using System;
using System.Diagnostics;
using System.Text.RegularExpressions;

// Drain both pipes without retaining raw output or credentials.
public sealed class TrainingOutput {
    public volatile int ActivePort;
    public volatile bool BindFailed;
    public volatile bool PortsExhausted;
    private readonly string healthAddress;
    public TrainingOutput(Process process, string healthAddress) {
        this.healthAddress = healthAddress;
        process.OutputDataReceived += Accept;
        process.ErrorDataReceived += Accept;
    }
    private void Accept(object sender, DataReceivedEventArgs args) {
        string line = args.Data;
        if (line == null) return;
        var match = Regex.Match(line, @"^ACTIVE_PORT=(3000|58080|61080)$");
        if (match.Success) ActivePort = int.Parse(match.Groups[1].Value);
        if (line == "MCP_PORTS_UNAVAILABLE") PortsExhausted = true;
        if (!string.IsNullOrEmpty(healthAddress)
            && line.Contains(healthAddress)
            && Regex.IsMatch(line, @"(?i)\b(bind|listen)\b")
            && Regex.IsMatch(line, @"(?i)address already in use|only one usage|access.+forbidden|permission denied|cannot assign requested address|not valid in its context|EADDRINUSE|EACCES|EADDRNOTAVAIL"))
            BindFailed = true;
    }
}
