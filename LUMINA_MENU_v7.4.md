# 🎨 Lumina v7.4 - Novo Menu Principal LED TOOLS

## 📋 Resumo da Atualização

**Versão:** 7.4  
**Data:** 20/10/2026  
**Mudança:** Menu principal redesenhado no estilo empresarial profissional  
**Inspiração:** Design de referência com cards brancos e ícones outline  

---

## 🎯 O Que Mudou

### **Menu Principal - 4 Cards Grandes**

Substituímos a navegação tradicional por **4 cards principais** que representam os módulos core do sistema:

#### 1. **⚡ Vendas e NF-e**
- **Ícone:** Raio (velocidade, energia)
- **Função:** Acesso rápido a orçamentos e pedidos de venda
- **Link:** `/vendas/orcamento/`

#### 2. **💼 Produtos e Serviços**
- **Ícone:** Maleta/Caixa (catálogo)
- **Função:** Gestão completa do cadastro de produtos
- **Link:** `/cadastro/produto/`

#### 3. **📦 Finanças**
- **Ícone:** Cubo 3D (gestão, estrutura)
- **Função:** Fluxo de caixa, contas a pagar/receber
- **Link:** `/financeiro/contapagar/`

#### 4. **🛒 Compras, estoque e produção**
- **Ícone:** Carrinho de compras
- **Função:** Orçamentos/pedidos de compra e estoque
- **Link:** `/compras/orcamento/`

---

## 🎨 Design System

### **Cores**

```css
/* Cards */
Background:      #ffffff (branco limpo)
Border:          #e5e7eb (cinza claro)
Border Radius:   12px (arredondado)

/* Hover */
Border Hover:    #FF9100 (laranja LED TOOLS)
Shadow Hover:    0 4px 12px rgba(255, 145, 0, 0.15)
Transform:       translateY(-2px) (elevação)

/* Active State */
Background:      #FFF3E0 (laranja suave)
Border:          #FF9100 (laranja)
Color:           #FF9100 (texto laranja)
```

### **Tipografia**

```css
/* Cards Principais */
Font Size:       15px
Font Weight:     700 (negrito)
Color:           #0f172a (preto)
Color Active:    #FF9100 (laranja)

/* Cards Secundários */
Font Size:       14px
Font Weight:     600 (semi-negrito)
Color:           #0f172a
```

### **Ícones**

```css
/* Ícones Principais (SVG) */
Width:           32px
Height:          32px
Stroke Width:    2px
Stroke:          currentColor (herda cor do texto)
Fill:            none (outline style)

/* Ícones Secundários (SVG) */
Width:           20px
Height:          20px
Stroke Width:    2px
```

### **Espaçamento**

```css
/* Sidebar */
Width:           320px (antes: 240px)
Padding:         24px 16px
Background:      #fafbfc (cinza muito claro)

/* Cards Principais */
Padding:         20px
Gap (ícone):     16px
Margin Bottom:   12px (entre cards)

/* Cards Secundários */
Padding:         12px 16px
Gap (ícone):     12px
```

---

## 📊 Estrutura do Menu

```
MENU PRINCIPAL (4 cards grandes)
├── ⚡ Vendas e NF-e
├── 💼 Produtos e Serviços
├── 📦 Finanças
└── 🛒 Compras, estoque e produção

CADASTROS (3 itens)
├── 👥 Clientes
├── 🏢 Fornecedores
└── 🏭 Empresas

FISCAL (1 item)
└── 📄 Notas Fiscais

SISTEMA (3 itens)
├── 🏠 Dashboard
├── ⚙️ Meu Perfil
└── 👤 Usuários
```

---

## 🔧 Código CSS - Classes Principais

### **.menu-card** (Cards Grandes)

```css
.menu-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    color: #0f172a;
    text-decoration: none;
    font-size: 15px;
    font-weight: 700;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.menu-card:hover {
    border-color: #FF9100;
    box-shadow: 0 4px 12px rgba(255, 145, 0, 0.15);
    transform: translateY(-2px);
}

.menu-card.active {
    background: #FFF3E0;
    border-color: #FF9100;
    color: #FF9100;
}
```

### **.menu-icon** (Ícones SVG Grandes)

```css
.menu-icon {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    stroke: currentColor;
    fill: none;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}
```

### **.sidebar-nav a** (Cards Secundários)

```css
.sidebar-nav a {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    color: #0f172a;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s ease;
}

.sidebar-nav a:hover {
    border-color: #cbd5e1;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
}

.sidebar-nav a.active {
    background: #FFF3E0;
    border-color: #FF9100;
    color: #FF9100;
}
```

---

## 🎯 Ícones SVG Utilizados

### **Vendas (Raio)**
```html
<svg class="menu-icon" viewBox="0 0 24 24">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
</svg>
```

### **Produtos (Maleta)**
```html
<svg class="menu-icon" viewBox="0 0 24 24">
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
</svg>
```

### **Finanças (Cubo)**
```html
<svg class="menu-icon" viewBox="0 0 24 24">
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
    <line x1="12" y1="22.08" x2="12" y2="12"></line>
</svg>
```

### **Compras (Carrinho)**
```html
<svg class="menu-icon" viewBox="0 0 24 24">
    <circle cx="9" cy="21" r="1"></circle>
    <circle cx="20" cy="21" r="1"></circle>
    <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
</svg>
```

### **Clientes (Usuários)**
```html
<svg class="icon" viewBox="0 0 24 24">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
    <circle cx="9" cy="7" r="4"></circle>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
</svg>
```

---

## 📈 Antes vs Depois

| Característica | ❌ v7.3 | ✅ v7.4 |
|----------------|---------|---------|
| **Estilo** | Links simples | Cards brancos |
| **Ícones** | Emojis | SVG outline |
| **Tipografia** | 500 (medium) | 700 (bold) |
| **Hover** | Fundo cinza | Borda laranja + elevação |
| **Sidebar** | 240px | 320px |
| **Sombras** | Nenhuma | Sutil + hover |
| **Organização** | Lista plana | Cards + seções |
| **Visual** | Básico | **Empresarial profissional** ✨ |

---

## 🚀 Como Usar

### **1. Navegação por Cards Principais**

Os 4 cards principais no topo do menu levam diretamente aos módulos mais usados:
- Clique em **"Vendas e NF-e"** para acessar orçamentos/pedidos
- Clique em **"Produtos e Serviços"** para o cadastro de produtos
- Clique em **"Finanças"** para contas a pagar/receber
- Clique em **"Compras, estoque e produção"** para compras/estoque

### **2. Navegação por Seções**

Use as seções organizadas abaixo para:
- **Cadastros:** Clientes, Fornecedores, Empresas
- **Fiscal:** Notas Fiscais
- **Sistema:** Dashboard, Perfil, Usuários

### **3. Estados Visuais**

- **Normal:** Card branco com borda cinza
- **Hover:** Borda laranja + sombra + elevação (-2px)
- **Active:** Fundo laranja suave + borda laranja + texto laranja

---

## 🎨 Personalização

### **Alterar Cores**

Edite o arquivo `base.html` e modifique:

```css
/* Cor principal LED TOOLS */
#FF9100  → Sua cor primária
#E67E00  → Hover mais escuro
#FFF3E0  → Fundo suave (10% da cor)
```

### **Alterar Ícones**

Substitua os SVG paths pelos ícones de sua preferência:
- Fonte recomendada: [Feather Icons](https://feathericons.com/)
- Fonte alternativa: [Heroicons](https://heroicons.com/)

### **Alterar Textos dos Cards**

Edite os labels no HTML:

```html
<a href="..." class="menu-card">
    <svg>...</svg>
    Seu Texto Aqui
</a>
```

---

## 📱 Responsividade

O menu atual é otimizado para desktop. Para mobile:

```css
@media (max-width: 768px) {
    .sidebar {
        width: 100%;
        border-right: none;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .menu-card {
        font-size: 14px;
        padding: 16px;
    }
    
    .menu-icon {
        width: 28px;
        height: 28px;
    }
}
```

---

## ✅ Checklist de Implementação

- [x] Cards grandes para módulos principais
- [x] Ícones SVG outline profissionais
- [x] Tipografia em negrito (700)
- [x] Hover com borda laranja LED TOOLS
- [x] Sombras sutis e elevação
- [x] Sidebar 320px
- [x] Fundo neutro (#fafbfc)
- [x] Seções organizadas
- [x] Estados active/hover funcionais
- [x] Documentação completa

---

## 🏆 Resultado Final

**Menu principal moderno e profissional** que:
- ✅ Segue o estilo da referência fornecida
- ✅ Mantém a identidade visual LED TOOLS
- ✅ Melhora significativamente a UX
- ✅ Usa ícones profissionais (não emojis)
- ✅ Apresenta hierarquia visual clara
- ✅ Oferece feedback visual rico (hover/active)

---

**═══════════════════════════════════════════════════**

## 💡 **LUMINA v7.4 - Menu Empresarial Profissional**

**🟧 LED TOOLS • Enterprise-Grade Design • 100% Moderno 🟧**

**═══════════════════════════════════════════════════**

**Arquivo:** `djangosige/templates/base/base.html`  
**Preview:** `NOVO_MENU_PREVIEW.html`  
**Data:** 20/10/2026
