import type { ExportSettings } from './exportOptions'

function injectBackground(svg: string, background: string): string {
  if (background === 'transparent') {
    return svg
  }

  const color = background === 'white' ? '#ffffff' : background
  const insertAt = svg.indexOf('>')
  if (insertAt === -1) {
    return svg
  }

  return `${svg.slice(0, insertAt + 1)}<rect width="100%" height="100%" fill="${color}"/>${svg.slice(insertAt + 1)}`
}

function sanitizeSvgForCanvas(svg: string): string {
  return svg
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<image\b[^>]*(?:href|xlink:href)=["']https?:[^"']*["'][^>]*\/?>/gi, '')
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

function parseSvgDimensions(svg: string): { width: number; height: number } {
  const viewBoxMatch = svg.match(/viewBox="([^"]+)"/)
  if (viewBoxMatch) {
    const parts = viewBoxMatch[1].split(/\s+/).map(Number)
    if (parts.length === 4) {
      return { width: parts[2], height: parts[3] }
    }
  }

  const widthMatch = svg.match(/width="([\d.]+)/)
  const heightMatch = svg.match(/height="([\d.]+)/)
  return {
    width: widthMatch ? Number(widthMatch[1]) : 800,
    height: heightMatch ? Number(heightMatch[1]) : 600,
  }
}

async function svgToPng(svg: string, dpi: number, background: string): Promise<Blob> {
  const scale = dpi / 96
  const sanitized = sanitizeSvgForCanvas(svg)
  const { width, height } = parseSvgDimensions(sanitized)
  const canvas = document.createElement('canvas')
  canvas.width = Math.ceil(width * scale)
  canvas.height = Math.ceil(height * scale)

  const context = canvas.getContext('2d')
  if (!context) {
    throw new Error('Canvas is not supported in this browser')
  }

  if (background !== 'transparent') {
    const color = background === 'white' ? '#ffffff' : background
    context.fillStyle = color
    context.fillRect(0, 0, canvas.width, canvas.height)
  }

  const dataUrl = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(sanitized)}`

  const image = await new Promise<HTMLImageElement>((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = () => reject(new Error('Failed to load SVG for PNG export'))
    img.src = dataUrl
  })

  context.drawImage(image, 0, 0, canvas.width, canvas.height)

  return await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((result) => {
      if (result) {
        resolve(result)
      } else {
        reject(new Error('Failed to create PNG blob'))
      }
    }, 'image/png')
  })
}

export async function exportDiagram(svg: string, settings: ExportSettings): Promise<void> {
  const prepared = injectBackground(svg, settings.background)

  if (settings.format === 'svg') {
    downloadBlob(new Blob([prepared], { type: 'image/svg+xml;charset=utf-8' }), settings.filename)
    return
  }

  const pngBlob = await svgToPng(prepared, settings.dpi, settings.background)
  downloadBlob(pngBlob, settings.filename)
}
