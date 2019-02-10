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
 *     name_botanical: 'treeus fancyus',
 *     name_common: 'tree',
 *     family_name_botanical: 'familyus',
 *     height_group: 1,
 *     latitude: 123.456,
 *     longitude: 456.679,
 *     nativity: 'native',
 *     eol_id: 12345
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

  const species  = toMap(parseCsv(readFile('data/species_names.csv')), 'botanical_name')
  const nativity = toMap(parseCsv(readFile('data/species_native_status_EOL_ID.csv')), 'botanical_name')
  const treesRaw = parseCsv(csvRaw)

  const trees = treesRaw.map(t => {
    const botanical = t['Name Botanical']
    return {
      'name_botanical':        botanical,
      'name_common':           t['Name Common'],
      'family_name_botanical': getOrDefault(species, botanical, 'family_botanical_name', 'Unknown'),
      'height_group':          t['Height Group'],
      'latitude':              t['Latitude'],
      'longitude':             t['Longitude'],
      'nativity':              getOrDefault(nativity, botanical, 'native', 'Unknown'),
      'eol_id':                getOrDefault(nativity, botanical, 'EOL_ID', -1)
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
