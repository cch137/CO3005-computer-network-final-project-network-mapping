"use client"

import { useState } from "react"
import { Settings, ChevronDown, ChevronUp, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { type NetworkSettings, defaultSettings } from "@/types/settings"
import { useTheme } from "next-themes"
import { cn } from "@/lib/utils"
import { Switch } from "@/components/ui/switch"

interface SettingsPanelProps {
  settings: NetworkSettings
  onSettingsChange: (settings: NetworkSettings) => void
}

export default function SettingsPanel({ settings, onSettingsChange }: SettingsPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { resolvedTheme } = useTheme()
  const theme = resolvedTheme || "light"

  const updateSetting = <K extends keyof NetworkSettings>(key: K, value: NetworkSettings[K]) => {
    onSettingsChange({
      ...settings,
      [key]: value,
    })
  }

  const resetSettings = () => {
    onSettingsChange(defaultSettings)
  }

  return (
    <div
      className={cn(
        "fixed left-4 bottom-4 z-10 w-72 rounded-lg border shadow-lg",
        theme === "dark" ? "bg-[#44475a] border-[#6272a4] text-white" : "bg-white border-gray-200 text-gray-900",
        "transition-all duration-200",
        isOpen ? "opacity-95" : "opacity-80 hover:opacity-100",
      )}
    >
      <div className="w-full sticky top-0 z-20">
        <Button
          variant="ghost"
          className={cn(
            "flex w-full items-center justify-between p-4 rounded-lg",
            theme === "dark" ? "hover:bg-[#4d5066] text-[#f8f8f2]" : "hover:bg-gray-100",
            "transition-colors",
          )}
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="flex items-center">
            <Settings className="mr-2 h-5 w-5" />
            <span className="font-medium">網路拓撲圖設置</span>
          </div>
          {isOpen ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
        </Button>
      </div>

      {isOpen && (
        <div className="p-4 space-y-6 overflow-y-auto" style={{ maxHeight: "calc(75vh - 60px)" }}>
          <div className="space-y-4">
            <h3 className={cn("font-medium", theme === "dark" ? "text-[#f8f8f2]" : "")}>節點設置</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="nodeSize" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  節點大小
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.nodeSize}
                </span>
              </div>
              <Slider
                id="nodeSize"
                min={2}
                max={32}
                step={1}
                value={[settings.nodeSize]}
                onValueChange={(value) => updateSetting("nodeSize", value[0])}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="fontSize" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  字體大小
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.fontSize}px
                </span>
              </div>
              <Slider
                id="fontSize"
                min={8}
                max={16}
                step={1}
                value={[settings.fontSize]}
                onValueChange={(value) => updateSetting("fontSize", value[0])}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="showAllIPs" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                顯示所有 IP 位址
              </Label>
              <Switch
                id="showAllIPs"
                checked={settings.showAllIPs}
                onCheckedChange={(checked) => updateSetting("showAllIPs", checked)}
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className={cn("font-medium", theme === "dark" ? "text-[#f8f8f2]" : "")}>連接設置</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="linkDistance" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  連接距離
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.linkDistance}
                </span>
              </div>
              <Slider
                id="linkDistance"
                min={0}
                max={200}
                step={5}
                value={[settings.linkDistance]}
                onValueChange={(value) => updateSetting("linkDistance", value[0])}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="linkWidth" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  連接寬度
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.linkWidth}
                </span>
              </div>
              <Slider
                id="linkWidth"
                min={0.5}
                max={16}
                step={0.5}
                value={[settings.linkWidth]}
                onValueChange={(value) => updateSetting("linkWidth", value[0])}
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className={cn("font-medium", theme === "dark" ? "text-[#f8f8f2]" : "")}>物理模擬設置</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="repulsionStrength" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  排斥力
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.repulsionStrength}
                </span>
              </div>
              <Slider
                id="repulsionStrength"
                min={-500}
                max={-10}
                step={10}
                value={[settings.repulsionStrength]}
                onValueChange={(value) => updateSetting("repulsionStrength", value[0])}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="friction" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  摩擦係數
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.friction}
                </span>
              </div>
              <Slider
                id="friction"
                min={0.05}
                max={0.9}
                step={0.05}
                value={[settings.friction]}
                onValueChange={(value) => updateSetting("friction", value[0])}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="alpha" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  初始溫度
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.alpha}
                </span>
              </div>
              <Slider
                id="alpha"
                min={0.1}
                max={1}
                step={0.05}
                value={[settings.alpha]}
                onValueChange={(value) => updateSetting("alpha", value[0])}
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="alphaDecay" className={theme === "dark" ? "text-[#f8f8f2]" : ""}>
                  溫度衰減
                </Label>
                <span className={cn("text-sm", theme === "dark" ? "text-[#f8f8f2]" : "text-gray-500")}>
                  {settings.alphaDecay}
                </span>
              </div>
              <Slider
                id="alphaDecay"
                min={0.001}
                max={0.1}
                step={0.001}
                value={[settings.alphaDecay]}
                onValueChange={(value) => updateSetting("alphaDecay", value[0])}
              />
            </div>
          </div>

          <div className="pt-2">
            <Button
              variant="outline"
              size="sm"
              className={cn("w-full", theme === "dark" ? "border-[#6272a4] hover:bg-[#4d5066]" : "")}
              onClick={resetSettings}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              重置為默認設置
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
