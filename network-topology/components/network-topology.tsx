"use client"

import { useRef, useEffect, useState } from "react"
import * as d3 from "d3"
import type { Node } from "@/types/node"
import { cn } from "@/lib/utils"
import { useToast } from "@/hooks/use-toast"
import type { NetworkSettings } from "@/types/settings"
import NodeDetails from "@/components/node-details"

interface NetworkTopologyProps {
  nodes: Node[]
  selectedNode: string | null
  onNodeSelect: (nodeIp: string) => void
  theme?: string
  settings: NetworkSettings
}

export default function NetworkTopology({
  nodes,
  selectedNode,
  onNodeSelect,
  theme = "light",
  settings,
}: NetworkTopologyProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null)
  const { toast } = useToast()
  const simulationRef = useRef<d3.Simulation<d3.SimulationNodeDatum, undefined> | null>(null)
  const [selectedNodeData, setSelectedNodeData] = useState<Node | null>(null)
  const [hoveredNeighbors, setHoveredNeighbors] = useState<Set<string>>(new Set())
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const graphNodesRef = useRef<any[]>([])
  const previousSelectedNodeRef = useRef<string | null>(null)

  // References to D3 selections for updates
  const nodeGroupRef = useRef<d3.Selection<any, any, any, any> | null>(null)
  const linkRef = useRef<d3.Selection<any, any, any, any> | null>(null)
  const labelsRef = useRef<d3.Selection<any, any, any, any> | null>(null)
  const graphInitializedRef = useRef<boolean>(false)
  const gRef = useRef<d3.Selection<any, any, any, any> | null>(null)

  // Create a map of IP addresses to nodes for quick lookup
  const nodeMap = new Map<string, Node>()
  nodes.forEach((node) => nodeMap.set(node.ip_addr, node))

  // Update selected node data when selectedNode changes
  useEffect(() => {
    if (selectedNode && nodeMap.has(selectedNode)) {
      setSelectedNodeData(nodeMap.get(selectedNode) || null)

      // Only focus if this is a new selection
      if (selectedNode !== previousSelectedNodeRef.current) {
        focusOnNode(selectedNode)
        previousSelectedNodeRef.current = selectedNode
      }
    } else {
      setSelectedNodeData(null)
      previousSelectedNodeRef.current = null
    }
  }, [selectedNode, nodeMap])

  // Calculate node size based on neighbor count
  const calculateNodeSize = (node: Node) => {
    if (!node.neighbours) return settings.nodeSize

    // Base size on neighbor count, but cap at 2x normal size
    const baseSize = node.name ? settings.nodeSize : settings.nodeSize * 0.8
    const neighborFactor = Math.min(1 + node.neighbours.length / 20, 2)
    return baseSize * neighborFactor
  }

  // Process nodes to create graph data
  const processData = () => {
    const graphNodes = nodes.map((node) => ({
      id: node.ip_addr,
      name: node.name || node.ip_addr,
      domains: node.domains || [],
      group: node.name ? 1 : 2, // Different groups for nodes with/without names
      neighbors: node.neighbours || [],
      size: calculateNodeSize(node),
    }))

    const graphLinks: { source: string; target: string }[] = []

    // Create links based on neighbors
    nodes.forEach((node) => {
      if (node.neighbours && node.neighbours.length > 0) {
        node.neighbours.forEach((neighborIp) => {
          // Only add the link if the neighbor exists in our node list
          if (nodeMap.has(neighborIp)) {
            graphLinks.push({
              source: node.ip_addr,
              target: neighborIp,
            })
          }
        })
      }
    })

    return { nodes: graphNodes, links: graphLinks }
  }

  // Function to focus on a specific node by IP
  const focusOnNode = (nodeIp: string) => {
    if (!svgRef.current || !zoomRef.current || !graphNodesRef.current.length || !gRef.current) return

    const nodeData = graphNodesRef.current.find((n) => n.id === nodeIp)
    if (!nodeData) return

    const svg = d3.select(svgRef.current)
    const width = containerRef.current?.clientWidth || 1000
    const height = containerRef.current?.clientHeight || 800

    // Get the current transform
    const currentTransform = d3.zoomTransform(svg.node() as Element)

    // Calculate the exact position to center the node
    // We need to account for any existing transform
    const scale = 2 // Zoom level
    const x = width / 2 - nodeData.x * scale
    const y = height / 2 - nodeData.y * scale

    // Create a new transform that centers the node exactly
    const newTransform = d3.zoomIdentity.translate(x, y).scale(scale)

    // Apply the transform with a smooth transition
    svg.transition().duration(750).call(zoomRef.current.transform, newTransform)
  }

  // Initial graph creation - only runs once when nodes change
  useEffect(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return

    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove()
    graphInitializedRef.current = false

    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight

    const svg = d3
      .select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height])

    // Create a group for the graph
    const g = svg.append("g")
    gRef.current = g

    // Add zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 8])
      .on("zoom", (event) => {
        g.attr("transform", event.transform)
      })

    zoomRef.current = zoom
    svg.call(zoom)

    // Process the data
    const graph = processData()
    graphNodesRef.current = graph.nodes

    // Create a force simulation with settings
    const sim = d3
      .forceSimulation(graph.nodes as d3.SimulationNodeDatum[])
      .force(
        "link",
        d3
          .forceLink(graph.links)
          .id((d: any) => d?.id || "")
          .distance(settings.linkDistance),
      )
      .force("charge", d3.forceManyBody().strength(settings.repulsionStrength))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "collision",
        d3.forceCollide().radius((d: any) => (d?.size || settings.nodeSize) * 1.2),
      )
      .velocityDecay(settings.friction)
      .alpha(settings.alpha)
      .alphaDecay(settings.alphaDecay)

    simulationRef.current = sim

    // Create links
    const link = g
      .append("g")
      .attr("stroke", theme === "dark" ? "#555" : "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(graph.links)
      .join("line")
      .attr("stroke-width", settings.linkWidth)

    linkRef.current = link

    // Create node groups
    const nodeGroup = g.append("g").selectAll("g").data(graph.nodes).join("g")
    nodeGroupRef.current = nodeGroup

    // Add circles to node groups
    nodeGroup
      .append("circle")
      .attr("r", (d: any) => d?.size || settings.nodeSize)
      .attr("fill", (d: any) =>
        d?.group === 1 ? (theme === "dark" ? "#8be9fd" : "#0284c7") : theme === "dark" ? "#bd93f9" : "#6366f1",
      )
      .attr("stroke", theme === "dark" ? "#f8f8f2" : "#fff")
      .attr("stroke-width", 1)
      .attr("cursor", "pointer")

    // Add IP labels (initially hidden unless showAllIPs is true)
    const labels = nodeGroup
      .append("text")
      .attr("dy", (d: any) => (d?.size || settings.nodeSize) * 1.5)
      .attr("text-anchor", "middle")
      .attr("font-size", settings.fontSize)
      .attr("fill", theme === "dark" ? "#f8f8f2" : "#333")
      .attr("pointer-events", "none")
      .style("opacity", settings.showAllIPs ? 1 : 0)
      .text((d: any) => d?.id || "")

    labelsRef.current = labels

    // Add event handlers to node groups
    nodeGroup
      .on("mouseover", (event, d: any) => {
        if (!d || !d.id) return // Guard against undefined data

        const nodeData = nodeMap.get(d.id)
        if (nodeData) {
          setHoveredNode(nodeData)

          // Create a set of neighboring IPs
          const neighbors = new Set<string>()
          if (nodeData.neighbours) {
            nodeData.neighbours.forEach((neighborIp) => neighbors.add(neighborIp))
          }
          setHoveredNeighbors(neighbors)

          // Show IP for this node if not already showing all IPs
          if (!settings.showAllIPs) {
            // Show IP for the hovered node
            d3.select(event.currentTarget).select("text").style("opacity", 1)

            // Show IP for neighboring nodes
            if (nodeData.neighbours) {
              nodeData.neighbours.forEach((neighborIp) => {
                nodeGroup
                  .filter((n: any) => n && n.id === neighborIp)
                  .select("text")
                  .style("opacity", 1)
              })
            }
          }
        }
      })
      .on("mouseout", (event, d: any) => {
        setHoveredNode(null)
        setHoveredNeighbors(new Set())

        // Hide all IPs unless selected or showAllIPs is true
        if (!settings.showAllIPs) {
          // Reset all labels
          nodeGroup.select("text").style("opacity", 0)

          // Keep selected node and its neighbors visible
          if (selectedNode) {
            // Show label for selected node
            nodeGroup
              .filter((n: any) => n && n.id === selectedNode)
              .select("text")
              .style("opacity", 1)

            // Show labels for neighbors of selected node
            const selectedNodeObj = nodeMap.get(selectedNode)
            if (selectedNodeObj && selectedNodeObj.neighbours) {
              selectedNodeObj.neighbours.forEach((neighborIp) => {
                nodeGroup
                  .filter((n: any) => n && n.id === neighborIp)
                  .select("text")
                  .style("opacity", 1)
              })
            }
          }
        }
      })
      .on("click", (event, d: any) => {
        event.stopPropagation()
        if (!d || !d.id) return // Guard against undefined data

        onNodeSelect(d.id)
      })
      .call(
        d3
          .drag<any, any>()
          .on("start", (event, d) => {
            if (!d) return // Guard against undefined data
            if (!event.active && simulationRef.current) simulationRef.current.alphaTarget(0.3).restart()
            d.fx = d.x
            d.fy = d.y
          })
          .on("drag", (event, d) => {
            if (!d) return // Guard against undefined data
            d.fx = event.x
            d.fy = event.y
          })
          .on("end", (event, d) => {
            if (!d) return // Guard against undefined data
            if (!event.active && simulationRef.current) simulationRef.current.alphaTarget(0)
            d.fx = null
            d.fy = null
          }),
      )

    // Update positions on each tick
    sim.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source?.x || 0)
        .attr("y1", (d: any) => d.source?.y || 0)
        .attr("x2", (d: any) => d.target?.x || 0)
        .attr("y2", (d: any) => d.target?.y || 0)

      nodeGroup.attr("transform", (d: any) => {
        if (!d || typeof d.x !== "number" || typeof d.y !== "number") {
          return "translate(0,0)" // Fallback for invalid data
        }
        return `translate(${d.x},${d.y})`
      })
    })

    // Handle window resize
    const handleResize = () => {
      if (!containerRef.current) return
      const newWidth = containerRef.current.clientWidth
      const newHeight = containerRef.current.clientHeight

      svg.attr("width", newWidth).attr("height", newHeight).attr("viewBox", [0, 0, newWidth, newHeight])

      sim.force("center", d3.forceCenter(newWidth / 2, newHeight / 2))
      sim.alpha(0.3).restart()
    }

    window.addEventListener("resize", handleResize)

    // Focus on selected node if any when graph is first created
    if (selectedNode) {
      // Wait for simulation to stabilize a bit
      setTimeout(() => {
        focusOnNode(selectedNode)
      }, 100)
    }

    graphInitializedRef.current = true

    return () => {
      window.removeEventListener("resize", handleResize)
      sim.stop()
    }
  }, [nodes, theme]) // Only re-render when nodes or theme changes, not settings

  // Handle clicking outside nodes to deselect
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (e.target === svgRef.current) {
        onNodeSelect("")
      }
    }

    document.addEventListener("click", handleClickOutside)
    return () => {
      document.removeEventListener("click", handleClickOutside)
    }
  }, [onNodeSelect])

  // Update node appearance when selected node changes without re-rendering the entire graph
  useEffect(() => {
    if (!svgRef.current || !simulationRef.current || !nodeGroupRef.current || !linkRef.current) return

    const nodeGroup = nodeGroupRef.current
    const link = linkRef.current

    // Reset all nodes to default appearance
    nodeGroup
      .select("circle")
      .attr("r", (d: any) => {
        if (!d) return settings.nodeSize
        const node = nodeMap.get(d.id)
        return node ? calculateNodeSize(node) : settings.nodeSize
      })
      .attr("stroke", theme === "dark" ? "#f8f8f2" : "#fff")
      .attr("stroke-width", 1)

    // Reset all text labels if not showing all IPs
    if (!settings.showAllIPs) {
      nodeGroup.select("text").style("opacity", 0)
    }

    // Reset all links
    link
      .attr("stroke", theme === "dark" ? "#555" : "#999")
      .attr("stroke-width", settings.linkWidth)
      .attr("stroke-opacity", 0.6)

    // No dimming of nodes when a node is selected
    nodeGroup.attr("opacity", 1)

    if (selectedNode) {
      const selectedNodeData = nodeMap.get(selectedNode)

      if (selectedNodeData) {
        // Highlight only the selected node
        nodeGroup
          .filter((d: any) => d && d.id === selectedNode)
          .select("circle")
          .attr("r", (d: any) => {
            const node = nodeMap.get(d.id)
            return node ? calculateNodeSize(node) * 1.2 : settings.nodeSize * 1.2
          })
          .attr("stroke", theme === "dark" ? "#ff79c6" : "#e11d48")
          .attr("stroke-width", 2)

        // Show IP for selected node if not showing all IPs
        if (!settings.showAllIPs) {
          // Show label for selected node
          nodeGroup
            .filter((d: any) => d && d.id === selectedNode)
            .select("text")
            .style("opacity", 1)

          // Show labels for neighbors of selected node
          if (selectedNodeData.neighbours) {
            selectedNodeData.neighbours.forEach((neighborIp) => {
              nodeGroup
                .filter((d: any) => d && d.id === neighborIp)
                .select("text")
                .style("opacity", 1)
            })
          }
        }

        // Highlight links connected to the selected node
        link
          .filter((d: any) => {
            if (!d || !d.source || !d.target) return false
            return d.source.id === selectedNode || d.target.id === selectedNode
          })
          .attr("stroke", theme === "dark" ? "#ff79c6" : "#e11d48")
          .attr("stroke-width", settings.linkWidth * 1.5)
          .attr("stroke-opacity", 1)
      }
    }
  }, [selectedNode, theme, settings.nodeSize, settings.linkWidth, settings.showAllIPs, nodeMap])

  // Update node labels when hoveredNode or hoveredNeighbors changes
  useEffect(() => {
    if (!svgRef.current || settings.showAllIPs || !nodeGroupRef.current) return

    const nodeGroup = nodeGroupRef.current

    // Show labels for hovered node and its neighbors
    if (hoveredNode) {
      // Show label for hovered node
      nodeGroup
        .filter((d: any) => d && d.id === hoveredNode.ip_addr)
        .select("text")
        .style("opacity", 1)

      // Show labels for neighboring nodes
      nodeGroup
        .filter((d: any) => d && hoveredNeighbors.has(d.id))
        .select("text")
        .style("opacity", 1)
    } else if (selectedNode) {
      // If no node is hovered but a node is selected, show label for selected node and its neighbors
      const selectedNodeData = nodeMap.get(selectedNode)

      // Show label for selected node
      nodeGroup
        .filter((d: any) => d && d.id === selectedNode)
        .select("text")
        .style("opacity", 1)

      // Show labels for neighbors of selected node
      if (selectedNodeData && selectedNodeData.neighbours) {
        selectedNodeData.neighbours.forEach((neighborIp) => {
          nodeGroup
            .filter((d: any) => d && d.id === neighborIp)
            .select("text")
            .style("opacity", 1)
        })
      }
    } else {
      // If no node is hovered or selected, hide all labels
      nodeGroup.select("text").style("opacity", 0)
    }
  }, [hoveredNode, hoveredNeighbors, selectedNode, settings.showAllIPs, nodeMap])

  // Update visualization based on settings changes without re-rendering
  useEffect(() => {
    if (
      !graphInitializedRef.current ||
      !simulationRef.current ||
      !nodeGroupRef.current ||
      !linkRef.current ||
      !labelsRef.current
    )
      return

    const simulation = simulationRef.current
    const nodeGroup = nodeGroupRef.current
    const link = linkRef.current
    const labels = labelsRef.current

    // Update node sizes
    nodeGroup
      .select("circle")
      .transition()
      .duration(300)
      .attr("r", (d: any) => {
        if (!d) return settings.nodeSize
        const node = nodeMap.get(d.id)
        return node ? calculateNodeSize(node) : settings.nodeSize
      })

    // Update font size
    labels
      .transition()
      .duration(300)
      .attr("font-size", settings.fontSize)
      .attr("dy", (d: any) => (d?.size || settings.nodeSize) * 1.5)

    // Update link width
    link.transition().duration(300).attr("stroke-width", settings.linkWidth)

    // Update label visibility based on showAllIPs
    if (settings.showAllIPs) {
      // Show all labels
      labels.style("opacity", 1)
    } else {
      // Reset all labels
      labels.style("opacity", 0)

      // If a node is selected, show its label and its neighbors' labels
      if (selectedNode) {
        const selectedNodeData = nodeMap.get(selectedNode)

        // Show label for selected node
        nodeGroup
          .filter((d: any) => d && d.id === selectedNode)
          .select("text")
          .style("opacity", 1)

        // Show labels for neighbors of selected node
        if (selectedNodeData && selectedNodeData.neighbours) {
          selectedNodeData.neighbours.forEach((neighborIp) => {
            nodeGroup
              .filter((d: any) => d && d.id === neighborIp)
              .select("text")
              .style("opacity", 1)
          })
        }
      }

      // If a node is hovered, show its label and its neighbors' labels
      if (hoveredNode) {
        // Show label for hovered node
        nodeGroup
          .filter((d: any) => d && d.id === hoveredNode.ip_addr)
          .select("text")
          .style("opacity", 1)

        // Show labels for neighboring nodes
        if (hoveredNeighbors.size > 0) {
          nodeGroup
            .filter((d: any) => d && hoveredNeighbors.has(d.id))
            .select("text")
            .style("opacity", 1)
        }
      }
    }

    // Update simulation forces
    simulation
      .force("link", d3.forceLink(simulation.force("link").links()).distance(settings.linkDistance))
      .force("charge", d3.forceManyBody().strength(settings.repulsionStrength))
      .force(
        "collision",
        d3.forceCollide().radius((d: any) => (d?.size || settings.nodeSize) * 1.2),
      )
      .velocityDecay(settings.friction)
      .alpha(settings.alpha)
      .alphaDecay(settings.alphaDecay)
      .alphaTarget(0.3)
      .restart()

    // Let the simulation run for a bit then stop it
    setTimeout(() => {
      if (simulationRef.current) {
        simulationRef.current.alphaTarget(0)
      }
    }, 300)
  }, [settings, nodeMap, hoveredNode, hoveredNeighbors, selectedNode])

  return (
    <div ref={containerRef} className="w-full h-full">
      <svg ref={svgRef} className={cn("w-full h-full", theme === "dark" ? "bg-[#282a36]" : "bg-[#f8fafc]")} />

      {/* Show node details for either hovered or selected node */}
      {(hoveredNode || selectedNodeData) && (
        <NodeDetails
          node={hoveredNode || selectedNodeData}
          nodeMap={nodeMap}
          theme={theme}
          isPinned={!!selectedNodeData && !hoveredNode}
        />
      )}
    </div>
  )
}
