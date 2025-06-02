<script setup lang="ts">
import SidebarLayout from './components/SidebarLayout.vue'
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
const isPublicRoute = computed(() => route.meta.public === true)
</script>

<template>
  <div class="h-screen flex flex-col">
    <SidebarLayout v-if="!isPublicRoute">
      <div class="h-full overflow-y-auto">
        <router-view />
      </div>
    </SidebarLayout>
    <router-view v-else />
  </div>
</template>

<style>
html, body, #app {
  height: 100%;
}
</style>
