Set oWS = WScript.CreateObject("WScript.Shell")
sDesktop = oWS.SpecialFolders("Desktop")

' Atalho 1: INSTALAR LED GERENCIAL
Set oLink = oWS.CreateShortcut(sDesktop & "\💡 Instalar Led Gerencial.lnk")
oLink.TargetPath = "C:\Users\Usuario\djangoSIGE\INSTALAR_LED_GERENCIAL.bat"
oLink.WorkingDirectory = "C:\Users\Usuario\djangoSIGE"
oLink.Description = "Instalar e iniciar Led Gerencial v7.5"
oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,21"
oLink.Save

' Atalho 2: INICIAR SERVIDOR
Set oLink = oWS.CreateShortcut(sDesktop & "\🚀 Led Gerencial - Iniciar.lnk")
oLink.TargetPath = "C:\Users\Usuario\djangoSIGE\INICIAR_SERVIDOR.bat"
oLink.WorkingDirectory = "C:\Users\Usuario\djangoSIGE"
oLink.Description = "Iniciar servidor Led Gerencial v7.5"
oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,14"
oLink.Save

' Atalho 3: ABRIR NO NAVEGADOR
Set oLink = oWS.CreateShortcut(sDesktop & "\🌐 Led Gerencial - Abrir.lnk")
oLink.TargetPath = "http://localhost:8000"
oLink.Description = "Abrir Led Gerencial v7.5 no navegador"
oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,14"
oLink.Save

' Atalho 4: PASTA DO PROJETO
Set oLink = oWS.CreateShortcut(sDesktop & "\📁 Led Gerencial - Pasta.lnk")
oLink.TargetPath = "C:\Users\Usuario\djangoSIGE"
oLink.Description = "Abrir pasta do Led Gerencial v7.5"
oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,4"
oLink.Save

WScript.Echo "✅ Atalhos criados na área de trabalho!" & vbCrLf & vbCrLf & _
             "💡 Instalar Led Gerencial" & vbCrLf & _
             "🚀 Led Gerencial - Iniciar" & vbCrLf & _
             "🌐 Led Gerencial - Abrir" & vbCrLf & _
             "📁 Led Gerencial - Pasta"
