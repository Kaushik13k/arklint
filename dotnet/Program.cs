using System.Diagnostics;
using System.Net.Http;
using System.Runtime.InteropServices;

const string Version = "1.0.0";
const string Repo = "Kaushik13k/arklint";

static string? GetBinaryName()
{
    if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux) && RuntimeInformation.OSArchitecture == Architecture.X64)
        return "arklint-linux-x86_64";
    if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX) && RuntimeInformation.OSArchitecture == Architecture.Arm64)
        return "arklint-darwin-arm64";
    if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows) && RuntimeInformation.OSArchitecture == Architecture.X64)
        return "arklint-windows-x86_64.exe";
    return null;
}

static string GetCachedBinaryPath()
{
    var cacheDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        ".arklint", "bin", Version);
    Directory.CreateDirectory(cacheDir);
    var name = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "arklint.exe" : "arklint";
    return Path.Combine(cacheDir, name);
}

var binaryName = GetBinaryName();
if (binaryName is null)
{
    Console.Error.WriteLine(
        $"arklint: no prebuilt binary for {RuntimeInformation.OSDescription} {RuntimeInformation.OSArchitecture}.\n" +
        "Install via pip: pip install arklint");
    return 1;
}

var binaryPath = GetCachedBinaryPath();

if (!File.Exists(binaryPath))
{
    var url = $"https://github.com/{Repo}/releases/download/v{Version}/{binaryName}";
    Console.Error.WriteLine($"Downloading arklint v{Version}...");

    using var client = new HttpClient(new HttpClientHandler { AllowAutoRedirect = true });
    client.DefaultRequestHeaders.Add("User-Agent", "arklint-dotnet-tool");

    var bytes = await client.GetByteArrayAsync(url);
    await File.WriteAllBytesAsync(binaryPath, bytes);

    if (!RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
    {
        var chmod = Process.Start("chmod", $"+x \"{binaryPath}\"");
        chmod?.WaitForExit();
    }

    Console.Error.WriteLine("Done.");
}

var psi = new ProcessStartInfo(binaryPath) { UseShellExecute = false };
foreach (var arg in args)
    psi.ArgumentList.Add(arg);

var process = Process.Start(psi)!;
process.WaitForExit();
return process.ExitCode;
