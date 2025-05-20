"use client"

import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "next-themes"
import { useState } from "react"
import { cn } from "@/lib/utils"

interface RefreshButtonProps {
  onRefresh: () => void
  isLoading?: boolean
}

export default function RefreshButton({ onRefresh, isLoading = false }: RefreshButtonProps) {
  const { resolvedTheme } = useTheme()
  const theme = resolvedTheme || "light"
  const [isRotating, setIsRotating] = useState(false)

  const handleRefresh = () => {
    if (isLoading || isRotating) return

    setIsRotating(true)
    onRefresh()

    // Reset rotation after animation completes
    setTimeout(() => {
      setIsRotating(false)
    }, 1000)
  }

  return (
    <div className="fixed right-16 bottom-4 z-10">
      <Button
        variant="outline"
        size="icon"
        className={cn(
          "bg-background/80 backdrop-blur-sm w-10 h-10",
          isLoading || isRotating ? "opacity-50 cursor-not-allowed" : "",
        )}
        onClick={handleRefresh}
        disabled={isLoading || isRotating}
      >
        <RefreshCw className={cn("h-5 w-5", isRotating ? "animate-spin" : "", isLoading ? "opacity-50" : "")} />
        <span className="sr-only">刷新拓撲圖</span>
      </Button>
    </div>
  )
}
