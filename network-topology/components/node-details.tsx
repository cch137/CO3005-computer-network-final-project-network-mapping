"use client"

import { cn } from "@/lib/utils"
import type { Node } from "@/types/node"

interface NodeDetailsProps {
  node: Node
  nodeMap: Map<string, Node>
  theme?: string
  isPinned?: boolean
}

export default function NodeDetails({ node, nodeMap, theme = "light", isPinned = false }: NodeDetailsProps) {
  return (
    <div
      className={cn(
        "absolute p-3 rounded-md shadow-lg z-20 max-w-xs",
        "border border-border",
        theme === "dark" ? "bg-[#44475a] text-[#f8f8f2]" : "bg-white text-gray-800",
        isPinned ? "right-4 top-4" : "right-4 top-4",
      )}
    >
      {isPinned && <div className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 rounded-full" />}
      <h3 className="font-bold">{node.name || node.ip_addr}</h3>
      <p className="text-sm mt-1">IP: {node.ip_addr}</p>
      {node.domains && node.domains.length > 0 && (
        <div className="mt-1">
          <p className="text-sm font-semibold">域名:</p>
          <ul className="text-xs mt-1 space-y-1 max-h-32 overflow-y-auto">
            {node.domains.map((domain, i) => (
              <li key={i}>{domain}</li>
            ))}
          </ul>
        </div>
      )}
      {node.neighbours && node.neighbours.length > 0 && (
        <div className="mt-1">
          <p className="text-sm font-semibold">鄰近節點: {node.neighbours.length}</p>
          <ul className="text-xs mt-1 space-y-1 max-h-32 overflow-y-auto">
            {node.neighbours.map((neighborIp, i) => {
              const neighbor = nodeMap.get(neighborIp)
              return (
                <li key={i} className="truncate">
                  {neighbor?.name || neighborIp}
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </div>
  )
}
