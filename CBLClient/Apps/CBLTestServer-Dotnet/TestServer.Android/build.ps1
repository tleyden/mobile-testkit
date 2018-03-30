param (
    [Parameter()][string]$Version,
    [Parameter()][int]$BuildNum,
    [switch]$Community
)

function Modify-Packages {
    $filename = $args[0]
    $ver = $args[1]
    $community = $args[2]

    $content = [System.IO.File]::ReadAllLines($filename)
    $regex = New-Object -TypeName "System.Text.RegularExpressions.Regex" ".*?<PackageReference Include=`"Couchbase\.Lite(.*?)`" Version=`"(.*?)`""
    for($i = 0; $i -lt $content.Length; $i++) {
        $line = $content[$i]
        $matches = $regex.Matches($line)
        if($matches.Count -gt 0) {
            $oldPackageName = $matches[0].Groups[1].Value;
            $packageName = $oldPackageName.Replace(".Enterprise", "")
            if(-Not $community) {
                $packageName = ".Enterprise" + $packageName;
            }

            $oldVersion = $matches[0].Groups[2]
            $line = $line.Replace("Couchbase.Lite$oldPackageName", "Couchbase.Lite$packageName").Replace($oldVersion, $ver)
            $content[$i] = $line
        }
    }

    [System.IO.File]::WriteAllLines($filename, $content)
}

Push-Location $PSScriptRoot
$VSRegistryKey = "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7"
$VSInstall = (Get-ItemProperty -Path $VSRegistryKey -Name "15.0") | Select-Object -ExpandProperty "15.0"
if(-Not $VSInstall) {
    throw "Unable to locate VS2017 installation"
}

$MSBuild = "$VSInstall\MSBuild\15.0\Bin\MSBuild.exe"

$version_to_use = $Version
if(-Not $version_to_use) {
    if(-Not $env:VERSION) {
        throw "Version not defined for this script!  Either pass it in as -Version or define an environment variable named VERSION"
    }

    $version_to_use = $env:VERSION
}

$build_num_to_use = $BuildNum
if(-Not $build_num_to_use) {
    if(-Not $env:BLD_NUM) {
        throw "Build Number not defined for this script!  Either pass it in as -BuildNum or define an environment variable named BLD_NUM"
    }

    $build_num_to_use = [int]$env:BLD_NUM
}

try {
    if($build_num_to_use -lt 538) {
        $Community = $true
    }

    $fullVersion = $version_to_use + "-b" + $build_num_to_use.ToString("D4")
    Modify-Packages "$PSScriptRoot\TestServer.Android.csproj" $fullVersion $Community
    Modify-Packages "$PSScriptRoot\..\TestServer\TestServer.csproj" $fullVersion $Community

    Push-Location ..\TestServer
    dotnet restore
    if($LASTEXITCODE -ne 0) {
        Write-Error "Restore failed for TestServer"
        exit 1
    }

    Pop-Location

    & $MSBuild /t:Restore
    if($LASTEXITCODE -ne 0) {
        Write-Error "Restore failed for TestServer.Android"
        exit 1
    }

    & $MSBuild /p:Configuration=Release /t:Rebuild
    & $MSBuild /p:Configuration=Release /t:SignAndroidPackage
    if($LASTEXITCODE -ne 0) {
        Write-Error "Build failed for TestServer.Android"
        exit 1
    }

    if(-Not (Test-Path "apk")) {
        New-Item -ItemType Directory "apk"
    }

    if(Test-Path "apk\TestServer.Android.apk") {
        Remove-Item "apk\TestServer.Android.apk"
    }
    
    $ApkPath = Resolve-Path ".\apk"

    Push-Location "bin\Release"
    try {
        Copy-Item TestServer.Android-Signed.apk $ApkPath\TestServer.Android.apk
    } finally {
        Pop-Location
    }
} finally {
    Pop-Location
}