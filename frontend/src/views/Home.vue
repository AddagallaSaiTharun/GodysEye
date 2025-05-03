<template>
  <main class="bg-light text-dark min-vh-100">
    <!-- Hero Section -->
    <section class="bg-white shadow py-5">
      <div class="container text-center">
        <h1 class="display-4 text-primary">Next-Gen Facial Recognition System</h1>
        <p class="lead text-muted mb-4">
          Powered by YOLOv8 & FaceNet for real-time, high-accuracy face detection and recognition—engineered for performance and privacy.
        </p>
        <button class="btn btn-primary btn-lg">View Demo</button>
      </div>
    </section>

    <!-- Features Section -->
    <section class="py-5 bg-light">
      <div class="container">
        <h2 class="text-center mb-4">Core Capabilities</h2>
        <div class="row">
          <FeatureCard icon="⚡" title="Real-time Detection" desc="YOLOv8 enables lightning-fast face detection in dynamic environments." />
          <FeatureCard icon="🧠" title="Deep Feature Matching" desc="FaceNet extracts facial embeddings for highly accurate identification." />
          <FeatureCard icon="📈" title="Scalable & Efficient" desc="Embeddings stored in a vector DB ensure instant search and comparison." />
          <FeatureCard icon="🛡️" title="Privacy First" desc="Supports federated learning and encrypted data handling." />
          <FeatureCard icon="🏙️" title="Versatile Deployment" desc="Ideal for security, retail, healthcare, and smart cities.Can be used in many applications" />
          <FeatureCard icon="🔬" title="Future Ready" desc="Roadmap includes GANs, stream processing & more privacy tools." />
        </div>
      </div>
    </section>

    <!-- Use Cases -->
    <section class="py-5">
      <div class="container">
        <h2 class="text-center mb-4">Real-World Applications</h2>
        <div class="row text-center">
          <UseCase icon="📋" title="Automated Attendance" />
          <UseCase icon="🛍️" title="Retail Personalization" />
          <UseCase icon="💳" title="Secure Transactions" />
          <UseCase icon="🎥" title="Smart Surveillance" />
        </div>
      </div>
    </section>

    <!-- Ethics Section -->
    <section class="py-5 bg-light">
      <div class="container">
        <h2 class="text-center mb-4">Ethical by Design</h2>
        <p class="text-center mx-auto" style="max-width: 800px;">
          Our system integrates ethical AI principles, ensuring data protection, transparency, and compliance with global regulations. Encryption, decentralized learning, and privacy controls are built in.
        </p>
      </div>
    </section>

    <!-- CTA Footer -->
    <footer class="bg-primary text-white py-5">
      <div class="container text-center">
        <h3 class="h3 mb-4">Experience the Future of Face Recognition</h3>
        <p class="mb-4">Explore our GitHub repo, try the demo, or contribute to our roadmap.</p>
        <a href="https://github.com/your-repo" target="_blank" class="btn btn-light btn-lg">GitHub Repository</a>
      </div>
    </footer>
  </main>
</template>

<script>
import FeatureCard from '../components/FeatureCard.vue';
import UseCase from '../components/UseCase.vue';

export default {
  name: "HomeView",
  components: {
    FeatureCard,
    UseCase
  }
}
</script>

<style scoped>
body {
  font-family: 'Arial', sans-serif;
}
</style>
