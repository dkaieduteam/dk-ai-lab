using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;

// Ties a child process to the lifetime of the PowerShell window that started it.
// When the window closes (X button, logoff, crash), Windows closes the job handle
// and terminates the child, so no hidden MCP keeps running with the sign-in values.
// Used only by the MCP-only launcher. New type name: an already-open console keeps working.
public sealed class TrainingJob : IDisposable {
    [StructLayout(LayoutKind.Sequential)]
    private struct BasicLimit {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ExtendedLimit {
        public BasicLimit BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    private const int JobObjectExtendedLimitInformation = 9;
    private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateJobObject(IntPtr attributes, string name);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(IntPtr job, int infoClass, ref ExtendedLimit info, uint length);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    private IntPtr handle;

    public TrainingJob() {
        handle = CreateJobObject(IntPtr.Zero, null);
        if (handle == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        ExtendedLimit info = new ExtendedLimit();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
        if (!SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ref info, (uint)Marshal.SizeOf(typeof(ExtendedLimit)))) {
            int error = Marshal.GetLastWin32Error();
            CloseHandle(handle);
            handle = IntPtr.Zero;
            throw new Win32Exception(error);
        }
    }

    // Returns false instead of throwing so the caller can warn and continue.
    public bool Assign(Process process) {
        if (handle == IntPtr.Zero || process == null) return false;
        return AssignProcessToJobObject(handle, process.Handle);
    }

    // Closing the handle terminates any process still in the job.
    public void Dispose() {
        if (handle != IntPtr.Zero) { CloseHandle(handle); handle = IntPtr.Zero; }
    }
}
