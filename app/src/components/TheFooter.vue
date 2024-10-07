<template>
  <nav mt-6 inline-flex gap-2 text-xl>
    <button icon-btn @click="toggleDark()">
      <Icon :icon="isDark ? 'carbon:moon' : 'carbon:sun'" />
    </button>
    <Icon icon="logo:github" class="x2" />
    <Icon
      icon="logo:github"
      class="icon-btn"
      rel="noreferrer"
      href="https://github.com/antfu-collective/vitesse-lite"
      target="_blank"
      title="GitHub"
    />
  </nav>
</template>
