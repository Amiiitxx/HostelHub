$base = "c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Hostel"
$manage = "$base\manage.py"
$apps = @("accounts","dashboard","students","hostel","allocations","fees","complaints","visitors","attendance","reports")
foreach ($app in $apps) {
    python $manage startapp $app
    Write-Host "Created: $app"
}
Write-Host "All apps created successfully"
