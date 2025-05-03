<template>
    <div class="col-md-4 mb-4">
        <div class="card shadow-sm">
            <div class="card-body text-center">
                <div class="display-4 mb-3">{{ icon }}</div>
                <h5 class="card-title">{{ title }}</h5>
                <p class="card-text">{{ desc }}</p>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'FeatureCard',
    props: {
        icon: {
            type: String,
            required: true
        },
        title: {
            type: String,
            required: true
        },
        desc: {
            type: String,
            required: true
        }
    }
}
</script>