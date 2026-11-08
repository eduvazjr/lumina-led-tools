/* Exportar tabelas para CSV e PDF.
 *
 * Toda tabela de lista ou relatório (.table ou .tabela) ganha os botões
 * "CSV" e "PDF". O que vai para o arquivo é o que está na tela: todas as
 * linhas do filtro aplicado (não só a página atual), na ordem mostrada,
 * sem a coluna de seleção e sem a de ações.
 */
(function () {
    'use strict';

    var URL_EXPORTAR = '/exportar/';
    var IGNORAR = '.form-table, .modal table, .anexos table, [data-sem-exportar]';

    function texto(el) {
        return (el ? el.textContent : '').replace(/\s+/g, ' ').trim();
    }

    function cookie(nome) {
        var m = document.cookie.match('(?:^|; )' + nome + '=([^;]*)');
        return m ? decodeURIComponent(m[1]) : '';
    }

    function csrf() {
        var campo = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return (campo && campo.value) || cookie('csrftoken');
    }

    function textoCelula(td) {
        var copia = td.cloneNode(true);
        copia.querySelectorAll('.sr-only, button, input, select, svg, script, .row-actions').forEach(function (e) { e.remove(); });
        copia.querySelectorAll('.sublinha, .cell-sub').forEach(function (e) { e.textContent = ' · ' + texto(e); });
        return texto(copia);
    }

    function colunasValidas(tabela) {
        var cab = tabela.tHead && tabela.tHead.rows[tabela.tHead.rows.length - 1];
        if (!cab) return null;
        var indices = [], nomes = [], alinhamentos = [];
        Array.prototype.forEach.call(cab.cells, function (th, i) {
            var nome = texto(th);
            var ehSelecao = th.classList.contains('col-check') || th.querySelector('input[type="checkbox"]');
            if (ehSelecao || !nome || /^a[çc][õo]es$/i.test(nome) || /^remover$/i.test(nome)) return;
            indices.push(i);
            nomes.push(nome);
            var direita = /(^|\s)(num|col-num|text-right|direita)(\s|$)/.test(th.className) ||
                getComputedStyle(th).textAlign === 'right';
            alinhamentos.push(direita ? 'direita' : 'esquerda');
        });
        return indices.length ? { indices: indices, nomes: nomes, alinhamentos: alinhamentos } : null;
    }

    function linhasDaTela(tabela) {
        if (window.jQuery && jQuery.fn.dataTable && jQuery.fn.dataTable.isDataTable(tabela)) {
            return jQuery(tabela).DataTable().rows({ search: 'applied', order: 'applied' }).nodes().toArray();
        }
        var corpo = tabela.tBodies[0];
        return corpo ? Array.prototype.slice.call(corpo.rows) : [];
    }

    function filtrosAtivos() {
        var partes = [];
        document.querySelectorAll('.chip.is-on').forEach(function (c) {
            var t = texto(c);
            if (t && !/^tod[oa]s$/i.test(t)) partes.push(t);
        });
        document.querySelectorAll('form[method="get"] select, form[method="get"] input[type="search"], form[method="get"] input[type="date"], form[method="get"] input[type="text"]').forEach(function (campo) {
            if (!campo.value) return;
            var label = campo.closest('label');
            var rotulo = label ? Array.prototype.filter.call(label.childNodes, function (n) { return n.nodeType === 3; })
                .map(function (n) { return n.textContent; }).join(' ').replace(/\s+/g, ' ').trim() : (campo.getAttribute('aria-label') || '');
            var valor = campo.tagName === 'SELECT' ? texto(campo.options[campo.selectedIndex]) : campo.value;
            if (campo.type === 'date' && /^\d{4}-\d{2}-\d{2}$/.test(valor)) valor = valor.split('-').reverse().join('/');
            partes.push((rotulo ? rotulo + ': ' : '') + valor);
        });
        var busca = document.getElementById('search-bar');
        if (busca && busca.value) partes.push('Busca: ' + busca.value);
        return partes;
    }

    function dadosDaTabela(tabela) {
        var cols = colunasValidas(tabela);
        var linhas = linhasDaTela(tabela).filter(function (tr) {
            return tr.cells.length > cols.indices[cols.indices.length - 1] && !tr.querySelector('.dataTables_empty');
        }).map(function (tr) {
            return cols.indices.map(function (i) { return textoCelula(tr.cells[i]); });
        });
        var rodape = null;
        if (tabela.tFoot && tabela.tFoot.rows.length) {
            var tf = tabela.tFoot.rows[0];
            if (tf.cells.length === tabela.tHead.rows[tabela.tHead.rows.length - 1].cells.length) {
                rodape = cols.indices.map(function (i) { return textoCelula(tf.cells[i]); });
            }
        }
        var titulo = texto(document.querySelector('.page-title')) || document.title.split(' | ')[0];
        var painel = tabela.closest('.painel, .section, .list-card');
        var tituloPainel = painel && texto(painel.querySelector('.painel-titulo, .section-title'));
        if (tituloPainel && tituloPainel !== titulo) titulo += ' · ' + tituloPainel;
        var trilha = Array.prototype.filter.call(document.querySelectorAll('.breadcrumb > span'), function (e) { return !e.classList.contains('breadcrumb-sep'); })
            .map(texto).filter(Boolean).join(' / ');
        var subtitulo = [trilha].concat(filtrosAtivos()).filter(Boolean).join(' · ');
        return { titulo: titulo, subtitulo: subtitulo, colunas: cols.nomes, alinhamentos: cols.alinhamentos, linhas: linhas, rodape: rodape };
    }

    function baixar(tabela, formato, botao) {
        var dados;
        try { dados = dadosDaTabela(tabela); } catch (e) { alert('Não foi possível ler a tabela para exportar.'); return; }
        var corpo = new FormData();
        corpo.append('dados', new Blob([JSON.stringify(dados)], { type: 'application/json' }), 'dados.json');
        var rotulo = botao.textContent;
        botao.disabled = true;
        botao.textContent = 'Gerando…';
        fetch(URL_EXPORTAR + formato + '/', {
            method: 'POST', body: corpo, credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf() }
        }).then(function (resposta) {
            if (!resposta.ok) return resposta.text().then(function (t) { throw new Error(t || 'Erro ao gerar o arquivo.'); });
            var disp = resposta.headers.get('Content-Disposition') || '';
            var nome = (disp.match(/filename="([^"]+)"/) || [])[1] || ('exportacao.' + formato);
            return resposta.blob().then(function (blob) {
                var link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = nome;
                document.body.appendChild(link);
                link.click();
                setTimeout(function () { URL.revokeObjectURL(link.href); link.remove(); }, 1000);
            });
        }).catch(function (erro) {
            alert(erro.message.length < 200 ? erro.message : 'Erro ao gerar o arquivo.');
        }).then(function () {
            botao.disabled = false;
            botao.textContent = rotulo;
        });
    }

    function criarBotoes(tabela) {
        var grupo = document.createElement('span');
        grupo.className = 'exportar';
        grupo.setAttribute('role', 'group');
        grupo.setAttribute('aria-label', 'Exportar tabela');
        ['csv', 'pdf'].forEach(function (formato) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'btn btn-sm btn-secundario';
            b.textContent = formato.toUpperCase();
            b.title = 'Baixar esta tabela em ' + formato.toUpperCase();
            b.addEventListener('click', function () { baixar(tabela, formato, b); });
            grupo.appendChild(b);
        });
        return grupo;
    }

    function preparar(tabela) {
        if (tabela.dataset.exportar === 'ok' || tabela.matches(IGNORAR) || !colunasValidas(tabela)) return;
        tabela.dataset.exportar = 'ok';
        var botoes = criarBotoes(tabela);
        var painel = tabela.closest('.painel, .section, .list-card, .card');
        var cabecalho = painel && Array.prototype.find.call(painel.children, function (el) {
            return el.matches('.painel-cabecalho:not(form), .section-header, .list-toolbar');
        });
        if (cabecalho && !cabecalho.querySelector('.exportar')) {
            cabecalho.appendChild(botoes);
        } else {
            var barra = document.createElement('div');
            barra.className = 'exportar-barra';
            barra.appendChild(botoes);
            var alvo = tabela.closest('.tabela-caixa, .table-wrap, .table-responsive') || tabela;
            alvo.parentNode.insertBefore(barra, alvo);
        }
    }

    function iniciar() {
        document.querySelectorAll('.app-content table.table, .app-content table.tabela').forEach(preparar);
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
    else iniciar();
    window.addEventListener('load', iniciar);
})();
