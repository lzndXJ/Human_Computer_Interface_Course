<script setup>
defineProps({
  description: {
    type: String,
    default: 'Nothing to show yet.',
  },
})
</script>

<template>
  <el-empty :description="description" :image-size="96">
    <slot />
  </el-empty>
</template>
