/**
 * This script expects stdin to contain tree JSON data. The data is expected to be an
 * array of objects with, at minimum, an 'eol_id' property, e.g.
 *
 * ```
 * [
 *   { eol_id: 12345 },
 *   { eol_id: 12346 },
 *   ...
 * ]
 * ```
 *
 * This script will output on stdout the same array of objects augmented with an 
 * 'images' property that contains an array of image URLs, e.g.
 *
 * ```
 * [
 *   { 
 *     eol_id: 12345,
 *     images: [ 'http://img1', 'http://img2' ]
 *   },
 *   ...
 * ]
 * ```
 */

const fs       = require('fs')
const got      = require('got')
const Parallel = require('async-parallel')
const sharp    = require('sharp')
const log      = require('./util.js').log
const mkdir    = require('./util.js').mkdir
const stdin    = require('./util.js').stdin

async function main() {
  let trees = JSON.parse(stdin())

  log('== Starting image downloads...')

  let images = {}

  trees.filter(t => t.eol_id > 0)
       .forEach(t => images[t.eol_id] = '')

  let eolIds = Object.keys(images)

  await Parallel.each(eolIds, async (eolId) => {
    const index = eolIds.indexOf(eolId) + 1

    try {
      const startTime = new Date().getTime()

      let result = await got(makeFetchUrl(eolId), { json: true })

      if (!result.body.taxonConcept.dataObjects) {
        return log(`(${index}/${eolIds.length}) No image available for ${eolId}. Skipping.`)
      }

      let imgUrl    = result.body.taxonConcept.dataObjects[0].eolMediaURL
      let extension = imgUrl.substring(imgUrl.lastIndexOf('.') + 1)
      let filename  = `${eolId}.${extension}`
      let filepath  = `build/img/${filename}`

      mkdir('build')
      mkdir('build/img')

      await new Promise(resolve => {
        got.stream(imgUrl).pipe(fs.createWriteStream(filepath)).on('finish', resolve)
      })

      let resizedData = await sharp(filepath).resize(1024, 1024, { fit: 'inside' })
                                             .toBuffer()
      fs.writeFileSync(filepath, resizedData)
      
      log(`(${index}/${eolIds.length}) Downloaded image for ${eolId} (${new Date().getTime() - startTime} ms).`)

      images[eolId] = 'https://storage.googleapis.com/public-tree-map/img/' + filename 
    } catch (error) {
      log(`(${index}/${eolIds.length}) Failed to fetch json for ${eolId}. Skipping.`)
    }
  }, 4)

  trees.forEach(t => t['images'] = images[t.eol_id] ? [images[t.eol_id]] : [])

  return trees
}

function makeFetchUrl(eolId) {
  return `http://eol.org/api/pages/1.0.json?id=${eolId}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false`
}

main()
