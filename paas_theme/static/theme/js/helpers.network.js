/* copied from 'https://github.com/acdh-oeaw/network-visualization/blob/main/examples/umd/popover.html' and adjusted for paas */

const createOverlay = () => {
    const overlay = document.createElement('div')
    overlay.setAttribute('id', 'nerv-overlay')
    overlay.style.position = 'fixed'
    overlay.style.top = 0
    overlay.style.left = 0
    overlay.style.right = 0
    overlay.style.bottom = 0
    overlay.style.display = 'none'
    document.body.appendChild(overlay)
    return overlay
}

const createPopoverContainer = () => {
    const popoverStyle = document.createElement('style')
    popoverStyle.appendChild(document.createTextNode(''))
    document.head.appendChild(popoverStyle)
    popoverStyle.sheet.insertRule(`
      [data-nerv-popover] {
        position: absolute;
        max-height: 200px;
        width: 300px;
        overflow-y: auto;
        background: white;
        border: 1px solid #ddd;
        display: none;
        padding: 10px;
        box-shadow: 0 4px 4px 0 rgba(0, 0, 0, 0.1);
      }
    `)
    const popover = document.createElement('div')
    popover.setAttribute('id', 'nerv-popover')
    popover.setAttribute('data-nerv-popover', true)
    popover.setAttribute('role', 'dialog')
    document.body.appendChild(popover)
    return popover
}

const overlay = createOverlay()
const popover = createPopoverContainer()

let isPopoverOpen = false
let previouslyFocusedElement = null

const showPopover = ({ x, y, node, onDismiss }) => {
    isPopoverOpen = true

    const content = createPopoverContent({ node, onDismiss })
    popover.appendChild(content)
    popover.style.display = 'block'

    previouslyFocusedElement = document.activeElement

    const rect = popover.getBoundingClientRect()
    const left =
        x + rect.width > window.innerWidth + window.pageXOffset
            ? x - rect.width
            : x
    const top =
        y + rect.height > window.innerHeight + window.pageYOffset
            ? y - rect.height
            : y

    popover.style.left = left + 'px'
    popover.style.top = top + 'px'
}

const hidePopover = () => {
    popover.style.display = 'none'
    popover.innerHTML = ''
    isPopoverOpen = false

    if (previouslyFocusedElement) {
        previouslyFocusedElement.focus()
        previouslyFocusedElement = null
    }
}

const handleNodeClick = createPopoverContent => ({ node, event }) => {
    if (isPopoverOpen) return

    const canvas = event.target

    const onDismiss = event => {
        document.removeEventListener('keyup', onEscape, false)
        overlay.removeEventListener('mousedown', onDismiss, false)
        overlay.style.display = 'none'
        hidePopover()
        /** Nudge ForceGraph to update hover state */
        canvas.dispatchEvent(
            new MouseEvent('mousemove', {
              view: window,
              bubbles: true,
              cancelable: true,
              clientX: event.clientX,
              clientY: event.clientY,
            })
          )
    }

    const onEscape = event => {
        if (event.key === 'Escape') {
            onDismiss()
        }
    }

    document.addEventListener('keyup', onEscape, false)
    overlay.addEventListener('mousedown', onDismiss, false)
    overlay.style.display = 'block'
    showPopover({
        node,
        x: event.pageX,
        y: event.pageY,
        onDismiss,
    })
}

// --- popover content ---

const createPopoverContent = ({ node, onDismiss }) => {
    
    const container = document.createElement('div')
    const detailsEndpoint = `${window.location.origin}/${node.type.toLowerCase()}/${node.id}?subview=minimal`
    //setLoader(true)
    const loaderDetails = document.createElement('div');

    fetch(`${detailsEndpoint}`).then(response => {

        if (!response.ok) {
            return response.statusText
        }
        return response.text()
    }).then(data => {
        loaderDetails.style.display = 'none'
        var parser = new DOMParser();
        var htmlDoc = parser.parseFromString(data, 'text/html');
        container.appendChild(htmlDoc.getElementById('popovercontent'));
        feather.replace();
    })
    
    
    loaderDetails.className = "spinner-grow";
    container.appendChild(loaderDetails)

    return container
}

