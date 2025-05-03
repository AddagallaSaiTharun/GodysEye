<template>
    <div class="col-md-3 mb-4">
      <div class="card p-4 text-center">
        <div class="display-4 mb-3">{{ icon }}</div>
        <h5 class="card-title">{{ title }}</h5>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'UseCase',
    props: {
      icon: {
        type: String,
        required: true
      },
      title: {
        type: String,
        required: true
      }
    }
  }
  </script>
  