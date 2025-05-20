export interface NetworkSettings {
  nodeSize: number
  fontSize: number
  linkDistance: number
  linkWidth: number
  repulsionStrength: number
  friction: number
  alpha: number
  alphaDecay: number
  showAllIPs: boolean
}

export const defaultSettings: NetworkSettings = {
  nodeSize: 20,
  fontSize: 10,
  linkDistance: 80,
  linkWidth: 8,
  repulsionStrength: -80,
  friction: 0.1,
  alpha: 0.3,
  alphaDecay: 0.02,
  showAllIPs: false,
}
