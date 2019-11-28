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
        return log(`(${index}/${eolIds.length}) No images available for ${eolId}. Skipping.`)
      }

      images[eolId] = images[eolId] || []

      for (let i = 0; i < result.body.taxonConcept.dataObjects.length; i++) {
        let image = await processImage(result.body.taxonConcept.dataObjects[i], eolId, i)
        images[eolId].push(image)
        log(`(${index}/${eolIds.length}) Downloaded image #${i + 1} for ${eolId} (${new Date().getTime() - startTime} ms).`)
      }
    } catch (error) {
      log(`(${index}/${eolIds.length}) Failed to fetch data for ${eolId}. Skipping.`)
    }
  }, 4)

  trees.forEach(t => t['images'] = images[t.eol_id] ? images[t.eol_id] : [])

  console.log(JSON.stringify(trees, null, 2))
}

async function processImage(data, eolId, index) {
  let imgUrl    = data.eolMediaURL
  let extension = imgUrl.substring(imgUrl.lastIndexOf('.') + 1)
  let filename  = `${eolId}_${index + 1}.${extension}`
  let filepath  = `build/img/${filename}`
  let author    = {
    name: data.rightsHolder ? data.rightsHolder.trim() : '',
    url : `https://eol.org/pages/${eolId}/media`,
  }

  mkdir('build')
  mkdir('build/img')

  await new Promise(resolve => {
    got.stream(imgUrl).pipe(fs.createWriteStream(filepath)).on('finish', resolve)
  })

  let resizedData = await sharp(filepath).resize(1024, 1024, { fit: 'inside' })
                                         .toBuffer()
  fs.writeFileSync(filepath, resizedData)
  
  return {
    url   : 'https://storage.googleapis.com/public-tree-map/img/' + filename,
    author: author
  }
}

function makeFetchUrl(eolId) {
  return `http://eol.org/api/pages/1.0.json?id=${eolId}&images_per_page=3&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false`
}

main()
