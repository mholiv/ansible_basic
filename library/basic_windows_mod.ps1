#!powershell

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args

$state = Get-AnsibleParam -obj $params -name "recursive" -default $True -ValidateSet $True, $False
$source = Get-AnsibleParam -obj $params -name "source" -failifempty $true
$destination = Get-AnsibleParam -obj $params -name "destination" -failifempty $true
$want_to_fail = Get-AnsibleParam -obj $params -name "want_to_fail" -default "no" -ValidateSet $True, $False




$result = New-Object psobject @{
changed = $false
s = $source
d = $destination
};

if ($want_to_fail -eq "yes") {
Fail-Json $result
} else {
Exit-Json $result
}



