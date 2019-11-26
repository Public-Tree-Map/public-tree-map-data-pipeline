/**
 * This script expects that stdin contains the tree CSV data. That means you could pipe
 * it in via curl:
 *
 * ```
 * curl "http://data-url" | node parse-trees.js > trees.json
 * ```
 *
 * Or you could pipe in a local file if you want to avoid network activity:
 *
 * ```
 * cat trees.csv | node parse-trees.js > trees.json
 * ```
 *
 * It will write JSON to stdout in the following format:
 *
 * ```
 * [
 *   {
 *     tree_id: 1234567,
 *     name_botanical: 'treeus fancyus',
 *     name_common: 'tree',
 *     family_name_botanical: 'familyus',
 *     family_name_common: 'informily',
 *     height_min_ft: 1,
 *     height_max_ft: 15,
 *     diameter_min_in: 6,
 *     diameter_max_in: 12,
 *     shade_production: 'dense',
 *     irrigation_requirements: 'minimal',
 *     form: 'rounded',
 *     type: 'evergreen',
 *     latitude: 123.456,
 *     longitude: 456.679,
 *     location_description: 'street',
 *     nativity: 'native',
 *     iucn_status: 'endangered',
 *     ipc_rating: 'moderate',
 *     ipc_url: 'https://website.com',
 *     eol_id: 12345,
 *     eol_url: 'https://eol.org/mah_tree',
 *     address: '123 Made Up Street',
 *     city: 'Santa Monica',
 *     state: 'CA'
 *   },
 *   ...
 * ]
 * ```
 */

const parse    = require('csv-parse/lib/sync')
const log      = require('./util.js').log
const readFile = require('./util.js').readFile
const stdin    = require('./util.js').stdin

function main() {
  log('== Starting tree parsing...')

  const startTime = new Date().getTime()

  const csvRaw = stdin()
  log(`== Stdin read... (${new Date().getTime() - startTime} ms)`)

  const stdinTime = new Date().getTime()

  const heritageTrees = toMap(parseCsv(readFile('data/heritage_trees.csv')), 'tree_id')
  const extraData = toMap(parseCsv(readFile('data/species_attributes.csv')), 'botanical_name')
  const treesRaw  = parseCsv(csvRaw)

  const trees = treesRaw.map(t => {
    const botanical = t['Name Botanical']
    return {
      'tree_id':                 t['Tree ID'],
      'species_id':              getOrDefault(extraData, botanical, 'Species ID', null),
      'name_botanical':          botanical,
      'name_common':             t['Name Common'],
      'family_name_botanical':   getOrDefault(extraData, botanical, 'family_botanical_name', 'Unknown'),
      'family_name_common':      getOrDefault(extraData, botanical, 'family_common_name', 'Unknown'),
      'height_min_ft':           t['Height Min'] || -1,
      'height_max_ft':           t['Height Max'] || -1,
      'diameter_min_in':         t['DBH Min'] || -1,
      'diameter_max_in':         t['DBH Max'] || -1,
      'shade_production':        getOrDefault(extraData, botanical, 'shade_production', 'Unknown'),
      'irrigation_requirements': getOrDefault(extraData, botanical, 'Irrigation_Requirements', 'Unknown'),
      'form':                    getOrDefault(extraData, botanical, 'form', 'Unknown'),
      'type':                    getOrDefault(extraData, botanical, 'type', 'Unknown'),
      'latitude':                t['Latitude'],
      'longitude':               t['Longitude'],
      'location_description':    t['Location Description'],
      'nativity':                getOrDefault(extraData, botanical, 'native', 'Unknown'),
      'iucn_status':             getOrDefault(extraData, botanical, 'simplified_IUCN_status', 'Unknown'),
      'ipc_rating':              getOrDefault(extraData, botanical, 'Cal_IPC_rating', 'Unknown'),
      'ipc_url':                 getOrDefault(extraData, botanical, 'Cal_IPC_url', ''),
      'eol_id':                  getOrDefault(extraData, botanical, 'EOL_ID', -1),
      'eol_url':                 getOrDefault(extraData, botanical, 'EOL_overview_URL', ''),
      'address':                 t['Address'] + ' ' + t['Street'],
      'city':                    'Santa Monica',
      'state':                   'CA',
      'heritage':                !!heritageTrees[t['Tree ID']] ||  false,
      'heritageYear':            getOrDefault(heritageTrees, t['Tree ID'], 'year_added', null),
      'heritageNumber':          getOrDefault(heritageTrees, t['Tree ID'], 'heritage_number', null),
      'heritageText':            getOrDefault(heritageTrees, t['Tree ID'], 'text', null)
    }
  })

  log(`== Parsed data... (${new Date().getTime() - stdinTime} ms)`)

  console.log(JSON.stringify(trees, null, 2))
}

function parseCsv(contents) {
  return parse(contents, { 
    columns: true,
    skip_empty_lines: true 
  })
}

function toMap(data, key) {
  const map = {}
  data.forEach(d => map[d[key]] = d)
  return map
}

function getOrDefault(map, key, field, defaultValue) {
  return map[key] && map[key][field] ? map[key][field] : defaultValue
}

main()
