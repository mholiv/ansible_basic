#!powershell
# The above line tells us that this is a powershell module

#These lines tell us that we want to import the Ansible powershell common library
#THis is analogous to the "this is magic" in python.
# WANT_JSON
# POWERSHELL_COMMON

#Here we create the Parse-Args Object. This is analogous to argument_spec in python
$params = Parse-Args $args

#Here we define all of the required and optional parameters
# The value of these variables is set equal to what people use in the playbook
# See: http://docs.ansible.com/ansible/developing_modules.html#windows-modules-checklist
$state = Get-AnsibleParam -obj $params -name "recursive" -default $True -ValidateSet $True, $False
$source = Get-AnsibleParam -obj $params -name "source" -failifempty $true
$destination = Get-AnsibleParam -obj $params -name "destination" -failifempty $true
$want_to_fail = Get-AnsibleParam -obj $params -name "want_to_fail" -default "no" -ValidateSet $True, $False

#Here we create the result object. We can pass in any number of return values.
#The only required return value is "changed". The value must be set to either $True or $False
$result = New-Object psobject @{
changed = $false
s = $source
d = $destination
};

#If things go wrong we send the result with Fail-Json instead of Exit-Json.
if ($want_to_fail -eq "yes") {
Fail-Json $result
} else {
Exit-Json $result
}



