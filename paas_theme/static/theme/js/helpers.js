function move_network(direction) {
    const minmaxbtn = document.querySelector('#moveegontwbtn');
    const egonetworkwrapper = document.querySelector('#egonetworkwrapper');
    const egonetwork = document.querySelector('#egonetwork_visualization');
    const nodeInfoContainer = document.querySelector('#node-info');
    if (direction === 'up') {
        document.querySelector('#egonet-tab').style.display = "none";
        $('[href="#daten"]').tab('show');
        nodeInfoContainer.classList.remove('d-none');
        nodeInfoContainer.classList.add('col-md-4');
        const bio = document.querySelector('article.bio')
        bio.prepend(egonetworkwrapper);
        egonetworkwrapper.dataset.status = '';
        egonetwork.classList.remove("col-md-12");
        egonetwork.classList.add("col-md-8");
        minmaxbtn.setAttribute('onclick', 'move_network("down")');
        minmaxbtn.innerHTML = '<i data-feather="minimize-2"></i>';
        feather.replace();
    } else {
        document.querySelector('#egonet-tab').style.display = "block";
        nodeInfoContainer.classList.add('d-none');
        nodeInfoContainer.classList.remove('col-md-4');
        document.querySelector('#egonet').append(egonetworkwrapper);
        minmaxbtn.setAttribute('onclick', 'move_network("up")');
        minmaxbtn.innerHTML = '<i data-feather="maximize-2"></i>';
        feather.replace();
        $("#egonet-tab").tab('show');
    }
}

function showNodeInfo(node) {
    window.open(node.url, '_blank');

    const egonetwork = document.querySelector('#egonetworkwrapper');
    if (egonetwork.dataset.status === 'minimized') { } else {
        const nodeInfoContainer = document.querySelector('#node-info');
        nodeInfoContainer.querySelector("[data-src='type']").innerHTML = node.type;
        nodeInfoContainer.querySelector("[data-src='link']").innerHTML = node.label;
        nodeInfoContainer.querySelector("[data-src='link']").href = node.url;
    }
}

function clearNodeInfo() {
    const nodeInfoContainer = document.querySelector('#node-info');
    if (nodeInfoContainer) {
        nodeInfoContainer.querySelector("[data-src='type']").innerHTML = '';
        nodeInfoContainer.querySelector("[data-src='link']").innerHTML = '';
        nodeInfoContainer.querySelector("[data-src='link']").href = '';
    }
}

/* http://live.datatables.net/nugeyewe/7/edit */
function hideSearchInputs(containerElement, columns) {
    for (i = 0; i < columns.length; i++) {
        if (columns[i]) {

            $(`#${containerElement} .filters th`).eq(i).show();
        } else {
            console.log($(`#${containerElement} th`).eq(i))
            $(`#${containerElement} .filters th`).eq(i).hide();

        }
    }
}

function createDataTable(containerElement, order, pageLength) {
    
    $(`#${containerElement} thead tr`)
        .clone(true)
        .addClass('filters')
        .appendTo(`#${containerElement} thead`);

    var table = $(`#${containerElement}`).DataTable({
        language: {
            "url": "https://cdn.datatables.net/plug-ins/1.10.19/i18n/German.json"
            },
        dom: "'<'row controlwrapper'<'col-sm-4'f><'col-sm-4'i><'col-sm-4 exportbuttons'Br>>'" +
            "'<'row'<'col-sm-12't>>'" +
            "'<'row'<'col-sm-6 offset-sm-6'p>>'",
        responsive: true,
        pageLength: pageLength,
        buttons: [{
            extend: 'copyHtml5',
            text: '<i class="far fa-copy"/>',
            titleAttr: 'Copy',
            className: 'btn-link',
            init: function (api, node, config) {
                $(node).removeClass('btn-secondary')
            }
        },
        {
            extend: 'excelHtml5',
            text: '<i class="far fa-file-excel"/>',
            titleAttr: 'Excel',
            className: 'btn-link',
            init: function (api, node, config) {
                $(node).removeClass('btn-secondary')
            }
        },
        {
            extend: 'pdfHtml5',
            text: '<i class="far fa-file-pdf"/>',
            titleAttr: 'PDF',
            className: 'btn-link',
            init: function (api, node, config) {
                $(node).removeClass('btn-secondary')
            }
        }],
        order: order,
        orderCellsTop: true,
        fixedHeader: true,
        initComplete: function () {
            var api = this.api();

            // For each column
            api
                .columns()
                .eq(0)
                .each(function (colIdx) {
                    // Set the header cell to contain the input element
                    var cell = $(`#${containerElement} .filters th`).eq(
                        $(api.column(colIdx).header()).index()
                    );
                    $(cell).html('<input type="text"/>');

                    // On every keypress in this input
                    $(
                        'input',
                        $(` #${containerElement} .filters th`).eq($(api.column(colIdx).header()).index())
                    )
                        .off('keyup change')
                        .on('keyup change', function (e) {
                            e.stopPropagation();

                            // Get the search value
                            $(this).attr('title', $(this).val());
                            var regexr = '({search})'; //$(this).parents('th').find('select').val();

                            var cursorPosition = this.selectionStart;
                            // Search the column for that value
                            api
                                .column(colIdx)
                                .search(
                                    this.value != ''
                                        ? regexr.replace('{search}', '(((' + this.value + ')))')
                                        : '',
                                    this.value != '',
                                    this.value == ''
                                )
                                .draw();

                            $(this)
                                .focus()[0]
                                .setSelectionRange(cursorPosition, cursorPosition);
                        });
                });
                hideSearchInputs(containerElement, api.columns().responsiveHidden().toArray());
        },
    });
    table.responsive.recalc();

    table.on('responsive-resize', function (e, datatable, columns) {
        hideSearchInputs(containerElement, columns);

    });
}

