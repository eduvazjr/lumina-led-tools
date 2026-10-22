Set oWS = WScript.CreateObject("WScript.Shell")
sDesktop = oWS.SpecialFolders("Desktop")

' Atalho CORRIGIDO: INSTALAR LED GERENCIAL (sobrescreve o antigo)
Set oLink = oWS.CreateShortcut(sDesktop & "\💡 Instalar Led Gerencial.lnk")
oLink.TargetPath = "C:\Users\Usuario\djangoSIGE\INSTALAR_CORRIGIDO.bat"
oLink.WorkingDirectory = "C:\Users\Usuario\djangoSIGE"
oLink.Description = "Instalar Led Gerencial v7.5 (VERSÃO CORRIGIDA - SQLite)"
oLink.IconLocation = "%SystemRoot%\System32\shell32.dll,21"
oLink.Save

WScript.Echo "✅ Atalho ATUALIZADO na área de trabalho!" & vbCrLf & vbCrLf & _
             "O atalho '💡 Instalar Led Gerencial' agora usa o script corrigido" & vbCrLf & _
             "que força SQLite e remove a variável DATABASE_URL do sistema."
