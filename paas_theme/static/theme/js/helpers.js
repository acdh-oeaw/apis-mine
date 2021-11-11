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
    const egonetwork = document.querySelector('#egonetworkwrapper');
    console.log(egonetwork.dataset.status)
    if (egonetwork.dataset.status === 'minimized') {
        window.open(node.url, '_blank');
     } else {
        const nodeInfoContainer = document.querySelector('#node-details');
        const detailsEndpoint = `${window.location.origin}/${node.type.toLowerCase()}/${node.id}?subview=minimal`;
        fetch(`${detailsEndpoint}`).then(response => {

            if (!response.ok) {
                return response.statusText
            }
            return response.text()
        }).then(data => {
            var parser = new DOMParser();
            var htmlDoc = parser.parseFromString(data, 'text/html');
            nodeInfoContainer.innerHTML = '';
            nodeInfoContainer.appendChild(htmlDoc.getElementById('popovercontent'));
            feather.replace();
        })
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

