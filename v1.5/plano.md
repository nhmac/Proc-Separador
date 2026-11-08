Quero publicar a versão 1.5 do Proc-Separador.

Na pasta v1.5 estão dois ficheiros que preparei noutra sessão:
- proc-separador-express.patch: diff feito contra o index.html publicado no GitHub Pages (versão 1.4)
- separador.html: a página completa já com as alterações

A fonte é web/separador.html e o site é gerado com build_pages.py (o repositório Proc-Separador não se edita à mão).

1. Aplica o patch a web/separador.html. Se não aplicar limpo por o fonte ser diferente do publicado, aplica as mesmas alterações à mão, usando o separador.html como referência. Não percas nada que só exista no fonte.

2. As alterações são: seletor obrigatório "Tipo de PDF" (Fotolivros / Álbuns ou Biscates, sem valor por omissão); no modo Biscates a etiqueta é a folha com "Encomenda N_N" visível e tudo o resto vai para A4-Normal; verificações cruzadas que recusam o PDF se não bater com o tipo escolhido; o tipo aparece no guia e no nome do trabalho; versão web 1.5.

3. Corre o build_pages.py e confirma que o sw.js ficou com uma chave de cache nova.

4. Mostra-me o diff antes de fazer commit. Depois faz commit com a mensagem "Versão 1.5: tipo de PDF Biscates" e push.
