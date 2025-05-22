export interface NetworkSettings {
  nodeSize: number
  fontSize: number
  linkLength: number
  linkWidth: number
  repulsionStrength: number
  showAllIPs: boolean
}

export const defaultSettings: NetworkSettings = {
  nodeSize: 20,
  fontSize: 10,
  linkLength: 100,
  linkWidth: 8,
  repulsionStrength: -80,
  showAllIPs: false,
}
