"use client"

import { useState, useEffect, useRef } from "react"
import { Search } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import type { Node } from "@/types/node"
import { cn } from "@/lib/utils"
import { useTheme } from "next-themes"
import Fuse from "fuse.js"

interface SearchBarProps {
  nodes: Node[]
  onNodeSelect: (nodeIp: string) => void
}

// Prepare node for search by adding a searchKey
const prepareNodesForSearch = (nodes: Node[]): (Node & { searchKey: string })[] => {
  return nodes.map((node) => {
    // Create a searchable string combining name, IP, and domains
    // Make sure to convert everything to lowercase for case-insensitive search
    const searchKey = [node.name || "", node.ip_addr, ...(node.domains || [])].filter(Boolean).join(" ").toLowerCase()

    return {
      ...node,
      searchKey,
    }
  })
}

export default function SearchBar({ nodes, onNodeSelect }: SearchBarProps) {
  const [open, setOpen] = useState(false)
  const [searchValue, setSearchValue] = useState("")
  const [searchResults, setSearchResults] = useState<Node[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const { resolvedTheme } = useTheme()
  const theme = resolvedTheme || "light"
  const [fuseInstance, setFuseInstance] = useState<Fuse<Node & { searchKey: string }> | null>(null)
  const [preparedNodes, setPreparedNodes] = useState<(Node & { searchKey: string })[]>([])

  // Prepare nodes with searchKey
  useEffect(() => {
    if (nodes.length > 0) {
      const prepared = prepareNodesForSearch(nodes)
      setPreparedNodes(prepared)

      // Configure Fuse.js with more lenient parameters
      const options: Fuse.IFuseOptions<Node & { searchKey: string }> = {
        includeScore: true,
        shouldSort: true,
        threshold: 0.6, // Higher threshold for more lenient matching
        location: 0,
        distance: 200, // Increased distance for better fuzzy matching
        minMatchCharLength: 1, // Allow single character matches
        useExtendedSearch: true,
        ignoreLocation: true, // Ignore where in the string the match occurs
        keys: ["searchKey"], // Only search the combined searchKey
      }

      setFuseInstance(new Fuse(prepared, options))
    }
  }, [nodes])

  const handleSearch = (value: string) => {
    setSearchValue(value)

    if (!value.trim() || !fuseInstance) {
      setSearchResults([])
      return
    }

    // Convert search value to lowercase for consistency
    const searchTerm = value.toLowerCase()

    // Use Fuse.js for fuzzy search
    const results = fuseInstance.search(searchTerm)

    // Map results back to original nodes
    const matchedNodes = results.map((result) => result.item)

    setSearchResults(matchedNodes.slice(0, 10))
  }

  const handleSelectNode = (node: Node) => {
    onNodeSelect(node.ip_addr)
    setOpen(false)
    setSearchValue("")
  }

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault()
        setOpen((prev) => !prev)
        setTimeout(() => {
          inputRef.current?.focus()
        }, 100)
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <div className="w-full max-w-md">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              "w-full justify-between",
              theme === "dark" ? "bg-[#44475a] text-[#f8f8f2] border-[#6272a4]" : "",
            )}
          >
            <div className="flex items-center gap-2">
              <Search className="h-4 w-4" />
              <span className="hidden sm:inline-block">搜尋節點 (名稱、IP 或域名)</span>
              <span className="sm:hidden">搜尋</span>
            </div>
            <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-xs font-medium opacity-100 sm:flex">
              <span className="text-xs">⌘</span>K
            </kbd>
          </Button>
        </PopoverTrigger>
        <PopoverContent className="p-0 w-[300px] sm:w-[400px]" align="start">
          <Command shouldFilter={false}>
            <CommandInput
              ref={inputRef}
              placeholder="搜尋名稱、IP 或域名..."
              value={searchValue}
              onValueChange={handleSearch}
            />
            <CommandList>
              {searchResults.length === 0 && searchValue ? (
                <CommandEmpty>沒有找到相符的節點</CommandEmpty>
              ) : (
                <CommandGroup heading={`搜尋結果 (${searchResults.length})`}>
                  {searchResults.map((node) => (
                    <CommandItem
                      key={node.ip_addr}
                      value={node.ip_addr}
                      onSelect={() => handleSelectNode(node)}
                      className="cursor-pointer"
                    >
                      <div className="flex flex-col w-full">
                        <span className="font-medium">{node.name || node.ip_addr}</span>
                        {node.name && <span className="text-xs text-muted-foreground">{node.ip_addr}</span>}
                        {node.domains && node.domains.length > 0 && (
                          <div className="text-xs text-muted-foreground max-h-16 overflow-y-auto">
                            {node.domains.map((domain, index) => (
                              <div key={index} className="truncate">
                                {domain}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  )
}
