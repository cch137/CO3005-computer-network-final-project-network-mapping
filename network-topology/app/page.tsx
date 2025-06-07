"use client";

import { useState, useEffect, useCallback } from "react";
import { useTheme } from "next-themes";
import NetworkTopology from "@/components/network-topology";
import SearchBar from "@/components/search-bar";
import ThemeToggle from "@/components/theme-toggle";
import SettingsPanel from "@/components/settings-panel";
import RefreshButton from "@/components/refresh-button";
import { Loader2 } from "lucide-react";
import type { Node } from "@/types/node";
import { type NetworkSettings, defaultSettings } from "@/types/settings";
import { useToast } from "@/hooks/use-toast";

export default function Home() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [settings, setSettings] = useState<NetworkSettings>(defaultSettings);
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { toast } = useToast();
  const [refreshing, setRefreshing] = useState(false);

  // Ensure component is mounted to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  const fetchNetworkData = useCallback(async () => {
    try {
      setLoading(true);
      // original api path: https://vector.cch137.link/cn-project/all-nodes
      const response = await fetch(
        "https://raw.githubusercontent.com/cch137/CO3005-computer-network-final-project-network-mapping/refs/heads/master/server/all-nodes-sample.json"
      );
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      const data = await response.json();
      setNodes(data.nodes || []);
      setError(null);
    } catch (err) {
      console.error("Error fetching network data:", err);
      setError("無法載入網路數據。請稍後再試。");
      toast({
        title: "載入失敗",
        description: "無法載入網路數據。請稍後再試。",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchNetworkData();
  }, [fetchNetworkData]);

  const handleNodeSelect = (nodeIp: string) => {
    setSelectedNode(nodeIp ? nodeIp : null);
  };

  const handleSettingsChange = (newSettings: NetworkSettings) => {
    setSettings(newSettings);
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchNetworkData();
  };

  // Use a safe theme value
  const theme = mounted ? resolvedTheme || "light" : "light";

  return (
    <main className="relative w-full h-screen overflow-hidden">
      {loading ? (
        <div className="absolute inset-0 flex items-center justify-center bg-background">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
          <span className="ml-2">載入網路拓撲圖...</span>
        </div>
      ) : error ? (
        <div className="absolute inset-0 flex items-center justify-center bg-background">
          <p className="text-destructive">{error}</p>
        </div>
      ) : (
        <>
          <div className="absolute inset-0 z-0">
            <NetworkTopology
              nodes={nodes}
              selectedNode={selectedNode}
              onNodeSelect={handleNodeSelect}
              theme={theme}
              settings={settings}
            />
          </div>
          <div className="absolute top-4 left-4 right-4 z-10 flex flex-col gap-4 md:flex-row md:items-center">
            <SearchBar nodes={nodes} onNodeSelect={handleNodeSelect} />
          </div>
          <ThemeToggle />
          <RefreshButton onRefresh={handleRefresh} isLoading={refreshing} />
          <SettingsPanel
            settings={settings}
            onSettingsChange={handleSettingsChange}
          />
        </>
      )}
    </main>
  );
}
