function move_network(direction) {
    const minmaxbtn = document.querySelector('#moveegontwbtn');
    const egonetworkwrapper = document.querySelector('#egonetworkwrapper');
    const egonetwork = document.querySelector('#egonetwork_visualization');
    const nodeInfoContainer = document.querySelector('#node-info');
    if (direction==='up') {
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
    if (egonetwork.dataset.status === 'minimized') {} else {
    const nodeInfoContainer = document.querySelector('#node-info');
    nodeInfoContainer.querySelector("[data-src='type']").innerHTML = node.type;
    nodeInfoContainer.querySelector("[data-src='link']").innerHTML = node.label;
    nodeInfoContainer.querySelector("[data-src='link']").href = node.url;
}
}