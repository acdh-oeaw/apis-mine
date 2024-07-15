var map;
var date;
let lst_dates = []
let lst_long_lat = []
let featGroupHistogis

function adjustSize() {
  map.invalidateSize();
}

function initMap(baseUrl, pk) {

  var dataurl = `${baseUrl}?person_id=${pk}`;
  //var map;

  iconSettings = {
    mapIconUrl: '<svg xmlns="http://www.w3.org/2000/svg"  fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-map-pin"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>',
    mapIconColor: '#cc756b',
    // mapIconColorInnerCircle: '#fff',
    //pinInnerCircleRadius: 48
  },

    // icon normal state
    divIcon = L.divIcon({
      className: "leaflet-data-marker",
      html: L.Util.template(iconSettings.mapIconUrl, iconSettings),
      iconAnchor: [12, 24],
      iconSize: [24, 24],
      popupAnchor: [0, -24]
    }),

    window.addEventListener("map:init", function (event) {
      map = event.detail.map;

      // Download GeoJSON data with Ajax
      fetch(dataurl)
        .then(function (resp) {
          return resp.json();
        })
        .then(function (data) {
          return data;
        })
        .then(function (data) {
          var jsonLayer = L.geoJson(data, {
            pointToLayer: function (feature, latlng) {
              return L.marker(latlng, { icon: divIcon });
            },
            onEachFeature: function onEachFeature(feature, layer) {
              var props = feature.properties;
              let relations = "";
              props.relations.forEach(function (element) {
                relations += `<li>${element.relation}</li>`;
                if (!lst_dates.includes(element.start_date) && element.start_date != null) {
                  lst_dates.push(element.start_date)
                };
                if (!lst_dates.includes(element.end_date) && element.end_date != null) {
                  lst_dates.push(element.end_date)
                };
                if (!lst_long_lat.includes(feature.geometry.coordinates)) {
                  lst_long_lat.push(feature.geometry.coordinates)
                }
              });
              var content = `<div><h3><a href=${props.url}>${props.name}</a></h3><p>${props.kind}<br/><ul class="maps-list">${relations}<ul></p></div>`;
              layer.bindPopup(content);
              layer.on('mouseover', e => {
                window.eventBus.emit('apismap.mouseover', e);
                e.target._icon.classList.add('activated')
                for (f in e.target.feature.properties.relations) {
                  let rel = e.target.feature.properties.relations[f]
                  let d_obj = document.querySelector(`.spacetime-graph circle[relid='${rel.id}']`)
                  if (d_obj) {
                    d_obj.closest('div').classList.add('dot-hover')
                    d_obj.classList.add('hover')
                    document.querySelector(`.spacetime-graph circle[relid='${rel.id}'] + g.label-text`).classList.add('hover')
                  }
                }
              });
              layer.on('mouseout', e => {
                e.target._icon.classList.remove('activated');
                window.eventBus.emit('apismap.mouseout', e)
                document.querySelectorAll('.spacetime-graph circle').forEach(c => { c.classList.remove('hover') })
                document.querySelectorAll('.spacetime-graph g.label-text').forEach(c => { c.classList.remove('hover') })
                document.querySelector('div.spacetime-graph').classList.remove('dot-hover')
              }

              )
            }
          });
          jsonLayer.addTo(map);

          var bounds = jsonLayer.getBounds();
          if (JSON.stringify(bounds['_northEast']) === JSON.stringify(bounds['_southWest'])) {
            map.setView(bounds['_northEast'], 12);
          } else {
            /* workaround we need because map is initially hidden in tab */
            $('#map-container').data("bounds", jsonLayer.getBounds());
          }
        })
        .then(function () {
          console.log('event issued');
          window.eventBus.emit('apismap.marker.loaded')
        })
    });

}


async function add_histogis_shape() {
  let colors_shapes = ['#302f2f', '#3388ff', '#229c41', '#b8252c', '#d1c847']
  const featHistoGIS = []
  let list_permalinks = [];
  let histogis_url = new URL('https://histogis.acdh.oeaw.ac.at/api/where-was')
  const parsed_dates = lst_dates.map(d => Date.parse(d))
  const min_date = Math.min(...parsed_dates)
  const max_date = Math.max(...parsed_dates)
  const ts = (max_date + min_date) / 2
  date = new Date(ts)
  const listHistoGIS = []
  const preList = {}
  let count_runs = 0

  const hgis_requests = lst_long_lat.map(function (coords) {
    histogis_url.search = new URLSearchParams({
      lat: coords[1],
      lng: coords[0],
      when: date.toLocaleDateString('en-UK'),
      page_size: 15
    });
    return fetch(histogis_url)
      .then(res => res.json())
      .then(res => listHistoGIS.push(...res.features))
  })
  await Promise.all(hgis_requests)
  listHistoGIS.forEach(ft => {
    var count = 0
    let lst_perm = []
    ft.properties.parents.forEach(pr => {
      listHistoGIS.forEach(ft2 => {
        let subst = ft2['@id'].replace(/^.*\/\/[^\/]+/, '')
        if (pr.permalink === subst && !lst_perm.includes(subst)) {
          count += 1
          lst_perm.push(subst)
        }
      })
    })
    if (count in preList) {
      if (!preList[count].some(ft3 => ft3['@id'] === ft['@id'])) {
        preList[count].push(ft)
      }
    } else {
      preList[count] = [ft,]
    }
  })
  for (var idx in preList) {
    let pn = `histogis${idx}`
    map.createPane(pn);
    map.getPane(pn).style.zIndex = parseInt(`4${idx}0`)

    preList[idx].forEach(ft3 => {
      let jsonLayer = L.geoJson(ft3, {
        'pane': `histogis${idx}`,
        'color': colors_shapes[idx]
      })
      jsonLayer.bindTooltip(
        `${ft3.properties.name} (${ft3.properties.start_date} - ${ft3.properties.end_date})`,
        {
          permanent: false,
          direction: 'center',
          className: 'countryLabel'
        }
      );
      featHistoGIS.push(jsonLayer)
    })
    featGroupHistogis = L.featureGroup(featHistoGIS).addTo(map)
    const bounds = featGroupHistogis.getBounds();
    if (JSON.stringify(bounds['_northEast']) === JSON.stringify(bounds['_southWest'])) {
      map.setView(bounds['_northEast'], 12);
    } else {
      map.fitBounds(featGroupHistogis.getBounds());
    }
  }

}

function minimize_map() {
  let url = new URL(window.location.href)
  url.searchParams.delete('mapview')
  history.replaceState(null, '{{object}}', [url])
  document.querySelector('#map-tab').style.display = "block";
  const maplifeline = document.querySelector('#maplifeline');

  const mapleaflet = document.querySelector('#map-container')

  document.querySelector('#map').append(maplifeline);
  const spacetime = document.querySelector('#spacetime-graph-content');
  mapleaflet.style.height = `${spacetime.offsetHeight}px`;
  document.querySelector('#mapcaption').remove();
  let min_icon = document.querySelector('#maplifelinebtn');
  min_icon.setAttribute('onclick', 'move_map()');
  min_icon.innerHTML = '<i data-feather="maximize-2"></i>';
  feather.replace();
  if (featGroupHistogis) {
    featGroupHistogis.remove();
  }
  map.invalidateSize();
  $('[href="#map"]').tab('show');
}

function move_map() {
  document.querySelector('#map-tab').style.display = "none";
  $('[href="#daten"]').tab('show');
  const map_element = document.querySelector('div.inline-map')
  const maplifeline = document.querySelector('#maplifeline')
  const bio = document.querySelector('article.bio')
  const main = document.querySelector('#main')
  const biotext = document.querySelector('#main-bio-text')
  const spacetime = document.querySelector('div#spacetime-graph-content')
  const rightpane = document.querySelector('#right-pane > article')
  const mapleaflet = map_element.querySelector('#map-container')
  bio.prepend(maplifeline)
  let height_space_time = spacetime.offsetHeight
  if (height_space_time > 500) {
    mapleaflet.style.height = `${height_space_time}px`
  } else {
    mapleaflet.style.height = "500px"
  }
  //spacetime.style.paddingTop = `${document.querySelector('div.entry-header').offsetHeight}px`

  //bio.insertBefore(map_element, biotext);
  //add_histogis_shape()
  map.invalidateSize()
  const caption = document.createElement("p")
  // caption.style.fontSize = '0.8em'
  // caption.style.fontStyle = 'italic'
  // caption.id = "mapcaption";
  // caption.innerHTML = `Die Polygone werden dynamisch aus <a href="https://histogis.acdh.oeaw.ac.at">HistoGIS</a> erstellt. 
  // Es werden die administrativen Einheiten für die Position aller Marker zum Zeitpunkt ${date.toLocaleDateString('de-DE')} 
  // (Mitte der bekannten Lebensspanne) geladen.`
  // //caption.appendChild(tnode)

  // bio.insertBefore(caption, main);
  let max_icon = document.querySelector('#maplifelinebtn')
  max_icon.setAttribute('onclick', 'minimize_map()')
  max_icon.innerHTML = '<i data-feather="minimize-2"></i>'
  feather.replace()
  let url = new URL(window.location.href)
  url.searchParams.set('mapview', 'true')
  history.replaceState(null, '{{object}}', [url])
}
window.eventBus.on('spacetime.mouseover', e => {
  let nm = e.detail[0][0].data.id
  for (l in map._layers) {
    if (!("feature" in map._layers[l])) {
      continue
    }
    if (map._layers[l].feature.geometry.type === "Point") {
      let lst_rels = map._layers[l].feature.properties.relations.map(x => (x.id))
      if (map._layers[l].feature.geometry.type === "Point" && lst_rels.includes(nm)) {
        map._layers[l]._icon.classList.add("activated")
      }
    }
  }
})

window.eventBus.on('spacetime.mouseout', e => {
  for (l in map._layers) {
    if (!("feature" in map._layers[l])) {
      continue
    }
    if (map._layers[l].feature.geometry.type === "Point") {
      if (map._layers[l]._icon.classList.contains("activated")) {
        map._layers[l]._icon.classList.remove("activated")
      }
    }
  }

})

document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const mapview = urlParams.get('mapview', false);
  window.eventBus.on('apismap.marker.loaded', function () {
    if (mapview) {
      move_map();
    }
  }
  )
});