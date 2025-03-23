Start-Sleep -Seconds 1
$folder = "C:\Users\Wesma\Pictures\Screenshots"

if (!(Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder | Out-Null
}

$screenshot = Get-ChildItem -Path $folder -Filter "*.png" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($screenshot -eq $null -or $screenshot.FullName -eq "") {
    Write-Output "🚫 No screenshot found!"
    exit
}

# API endpoint
$apiUrl = "http://localhost:8000/interview/ss"

# Use .NET WebClient to send multipart/form-data
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"
$fileBytes = [System.IO.File]::ReadAllBytes($screenshot.FullName)

$body = (
    "--$boundary",
    "Content-Disposition: form-data; name=`"file`"; filename=`"$($screenshot.Name)`"",
    "Content-Type: image/png$LF",
    [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes),
    "--$boundary--$LF"
) -join $LF

$headers = @{
    "Content-Type" = "multipart/form-data; boundary=$boundary"
}

$response = Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -Headers $headers
Write-Output "✅ Screenshot sent!"
$response | ConvertTo-Json -Depth 10
