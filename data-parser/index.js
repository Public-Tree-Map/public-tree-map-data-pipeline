const parse = require('csv-parse/lib/sync')
const fs    = require('fs')

const species  = toMap(parseCsv('species_names.csv'), 'botanical_name')
const nativity = toMap(parseCsv('species_native_status_EOL_ID.csv'), 'botanical_name')
const treesRaw = parseCsv('trees.csv')

const trees = treesRaw.map(t => {
  const botanical = t['Name Botanical']
  return {
    'name_botanical': botanical,
    'name_common': t['Name Common'],
    'family_name_botanical': getOrDefault(species, botanical, 'family_botanical_name', 'Unknown'),
    'height_group': t['Height Group'],
    'latitude': t['Latitude'],
    'longitude': t['Longitude'],
    'nativity': getOrDefault(nativity, botanical, 'native', 'Unknown'),
    'eol_id': getOrDefault(nativity, botanical, 'EOL_ID', -1)
  }
})

const prefix = 'app.setData('
const body   = JSON.stringify(trees, null, 2)
const suffix = ');'

fs.writeFileSync('data.js', prefix + body + suffix)

console.log('Complete!')


function parseCsv(filename) {
  const contents = fs.readFileSync(getPath(filename), 'utf8')
  return parse(contents, { 
    columns: true,
    skip_empty_lines: true 
  })
}

function getPath(filename) {
  return '../data/' + filename;
}

function toMap(data, key) {
  const map = {}
  data.forEach(d => map[d[key]] = d)
  return map
}

function getOrDefault(map, key, field, defaultValue) {
  return map[key] && map[key][field] ? map[key][field] : defaultValue
}
