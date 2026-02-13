<script setup>
/**
 * App.vue - Layout chính của ứng dụng Background Remover.
 *
 * Cấu trúc:
 * - Background animated orbs
 * - Header với logo gradient
 * - Main layout: Sidebar (Upload + Tools) | Content (Preview)
 * - Footer
 */
import ImageUploader from './components/ImageUploader.vue'
import ToolPanel from './components/ToolPanel.vue'
import ImagePreview from './components/ImagePreview.vue'
import { useImageStore } from './stores/imageStore'

const store = useImageStore()
</script>

<template>
  <div class="app-wrapper">
    <!-- Animated Background Orbs -->
    <div class="bg-orb bg-orb--purple"></div>
    <div class="bg-orb bg-orb--cyan"></div>
    <div class="bg-orb bg-orb--pink"></div>

    <!-- Header -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <div class="logo__icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#logo-gradient)" stroke-width="2">
              <defs>
                <linearGradient id="logo-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" style="stop-color:#a78bfa" />
                  <stop offset="100%" style="stop-color:#22d3ee" />
                </linearGradient>
              </defs>
              <path d="M21 12a9 9 0 0 0-9-9M21 12a9 9 0 0 1-9 9M21 12H3M12 3a9 9 0 0 0 0 18M12 3a9 9 0 0 1 0 18"/>
            </svg>
          </div>
          <h1 class="logo__text">
            <span class="gradient-text">BG Remover</span>
          </h1>
        </div>
        <p class="header-subtitle">Xóa nền ảnh chuyên nghiệp với AI</p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <!-- Sidebar -->
      <aside class="sidebar">
        <!-- Upload Section -->
        <div class="sidebar-section stagger-enter" style="animation-delay: 0.1s">
          <ImageUploader />
        </div>

        <!-- Tool Panel (luôn hiển thị) -->
        <div class="sidebar-section stagger-enter" style="animation-delay: 0.2s">
          <ToolPanel />
        </div>
      </aside>

      <!-- Preview Area -->
      <section class="content glass-card stagger-enter" style="animation-delay: 0.15s">
        <ImagePreview />
      </section>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <p>Background Remover v1.0 — Powered by OpenCV & Python</p>
    </footer>
  </div>
</template>

<style scoped>
.app-wrapper {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* === Header === */
.app-header {
  padding: 20px 32px;
  position: relative;
  z-index: 2;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo__icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 14px;
}

.logo__text {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.header-subtitle {
  font-size: 0.85rem;
  color: rgba(226, 232, 240, 0.4);
  margin-left: auto;
  font-family: 'Space Grotesk', sans-serif;
}

/* === Main Layout === */
.app-main {
  flex: 1;
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 24px;
  padding: 0 32px 24px;
  position: relative;
  z-index: 2;
}

/* === Sidebar === */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(100vh - 120px); /* Trừ đi header và padding */
  overflow-y: auto;
  padding-right: 8px; /* Để scrollbar không dính sát content */
}

/* Custom Scrollbar for Sidebar */
.sidebar::-webkit-scrollbar {
  width: 6px;
}
.sidebar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
}
.sidebar::-webkit-scrollbar-thumb {
  background: rgba(139, 92, 246, 0.2);
  border-radius: 4px;
}
.sidebar::-webkit-scrollbar-thumb:hover {
  background: rgba(139, 92, 246, 0.4);
}

.sidebar-section {
  width: 100%;
}

/* === Content === */
.content {
  padding: 20px;
  min-height: 500px;
}

/* === Footer === */
.app-footer {
  padding: 20px 32px;
  text-align: center;
  font-size: 0.75rem;
  color: rgba(226, 232, 240, 0.2);
  position: relative;
  z-index: 2;
}

/* === Transitions === */
.slide-up-enter-active {
  transition: all 0.5s ease;
}

.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* === Responsive === */
@media (max-width: 900px) {
  .app-main {
    grid-template-columns: 1fr;
    padding: 0 16px 16px;
  }

  .app-header {
    padding: 16px;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .header-subtitle {
    margin-left: 0;
  }
}
</style>
