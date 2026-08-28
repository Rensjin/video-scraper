$webclient = New-Object System.Net.WebClient
$webclient.Headers.Add('User-Agent', 'Mozilla/5.0')
$content = $webclient.DownloadString('https://api.github.com/repos/Rensjin/video-scraper')
Write-Host $content.Substring(0, 300)
