/**
 * This script expects full-populated tree data. It should only be run as the final
 * step in the pipeline, as it writes files directly instead of to stdout.
 *
 * Its job is to split a single master data file into two parts:
 *  - A trimmed-down version of the main file with only the components necessary
 *    to render the top-level map view
 *  - A series of single JSON files that contain the full details of a single tree,
 *    which could be used to render the tree detail view
 */

const parse    = require('csv-parse/lib/sync')
const fs       = require('fs')
const log      = require('./util.js').log
const readFile = require('./util.js').readFile
const mkdir    = require('./util.js').mkdir
const stdin    = require('./util.js').stdin

function main() {
  if (process.argv.length !== 3) {
    console.error('Usage: node split-trees.js <output directory>')
    process.exit()
  }

  const rootDirectory = __dirname + '/' + process.argv[2]
  const treeDirectory = rootDirectory + '/trees'
  const trees         = JSON.parse(stdin())
  const mapData       = [];

  mkdir(treeDirectory)

  trees.forEach(function(tree) {
    mapData.push(getMapData(tree))
    writeTree(treeDirectory, tree)
  });

  fs.writeFileSync(`${rootDirectory}/map.json`, JSON.stringify(mapData, null, 2))
}

function getMapData(tree) {
  return copyFields(tree, [
    'diameter_max_in',
    'diameter_min_in',
    'family_name_botanical',
    'family_name_common',
    'height_max_ft',
    'height_min_ft',
    'ipc_rating',
    'irrigation_requirements',
    'iucn_status',
    'latitude',
    'longitude',
    'name_botanical',
    'name_common',
    'nativity',
    'shade_production',
    'tree_id',
    'pruning_year',
    'pruning_zone',
    'heritage'
  ])
}

function writeTree(directory, tree) {
  fs.writeFileSync(`${directory}/${tree.tree_id}.json`, JSON.stringify(tree, null, 2))
}

function copyFields(object, fields) {
  const output = {}

  fields.forEach(function(field) {
    if (object[field] !== undefined) {
      output[field] = object[field]
    }
  })

  return output
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
