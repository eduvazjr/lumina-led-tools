Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\🚀 Deploy LED Gerencial.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\Users\Usuario\djangoSIGE\DEPLOY_AUTOMATICO.bat"
oLink.WorkingDirectory = "C:\Users\Usuario\djangoSIGE"
oLink.Description = "Deploy automático do LED Gerencial v7.5 no Railway"
oLink.IconLocation = "C:\Windows\System32\shell32.dll,165"
oLink.Save

WScript.Echo "✅ Atalho criado na Área de Trabalho!"
