import SwiftUI

/// LOC-01 screens: pre-prompt explanation (before any system dialog), state, controls, control log.
/// French texts follow docs/participant-text-fr.md section 2.1.
struct LocationView: View {
    @Bindable var module: LocationModule
    @State private var showPrePrompt = false
    @State private var confirmDelete = false

    private static let df: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd HH:mm:ss xxx"; return f
    }()
    private static let tf: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "HH:mm:ss"; return f
    }()
    private func fmt(_ d: Date?) -> String { d.map { Self.df.string(from: $0) } ?? "aucun" }

    var body: some View {
        List {
            Section {
                Text("VERSION D'ESSAI : non approuvée pour des données réelles. Les relevés restent en mémoire sur ce téléphone seulement, sont perdus à la fermeture de l'application, et ne sont ni exportés ni transmis.")
                    .font(.footnote).foregroundStyle(.orange)
            }
            Section("États (deux couches distinctes)") {
                row("État de la sonde", module.probeState.rawValue)
                row("État du système (iOS)", module.osLabel)
                row("Observé à", module.osObservedAt.map { Self.tf.string(from: $0) } ?? "jamais")
                row("Collecte en cours", module.isCollecting ? "oui" : "non")
                if module.probeState == .blockedByOS {
                    Text("Bloqué par le système : modifiez l'autorisation dans Réglages > Confidentialité et sécurité > Service de localisation > Sensor Probe. L'application ne redemandera pas en boucle.")
                        .font(.footnote)
                }
            }
            Section("Commandes") {
                switch module.probeState {
                case .off:
                    Button("Activer la localisation…") { module.logExplained(); showPrePrompt = true }
                case .on:
                    Button("Pause") { module.pause() }
                case .paused:
                    Button("Reprendre (à partir de maintenant, sans rattrapage)") { module.resume() }
                case .blockedByOS:
                    Button("Réessayer l'explication") { module.logExplained(); showPrePrompt = true }
                }
                Button("Supprimer les relevés…", role: .destructive) { confirmDelete = true }
                    .disabled(module.samples.isEmpty)
            }
            Section("Relevés (sans carte ni coordonnées affichées)") {
                row("Nombre", "\(module.samples.count)")
                row("Premier", fmt(module.firstSample))
                row("Dernier", fmt(module.latestSample))
                row("Plages de collecte continues", "\(module.segmentCount)")
                let g = module.gapStats
                row("Trous > \(Int(LocationModule.gapThresholdSeconds)) s (dans une plage)", "\(g.count)")
                row("Plus long trou", g.count == 0 ? "aucun" : "\(Int(g.longest)) s")
                row("Pauses volontaires", "\(module.pausedIntervals.count)")
                row("Relevés invalides écartés", "\(module.discardedInvalid)")
                row("Méthode", LocationModule.method)
                row("Précision demandée / intervalle min.", "\(LocationModule.desiredAccuracyLabel) / \(Int(LocationModule.minIntervalSeconds)) s")
                Text("Un trou est un trou : il ne prouve ni immobilité ni absence. Tant que l'écran de l'application n'est pas affiché, aucun relevé n'est pris.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            Section("Journal des commandes (CTL-01)") {
                if module.controlLog.isEmpty { Text("aucun événement").foregroundStyle(.secondary) }
                ForEach(module.controlLog.reversed()) { e in
                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(Self.tf.string(from: e.time))  \(e.action)").font(.callout)
                        Text("sonde \(e.probeBefore.rawValue) → \(e.probeAfter.rawValue) · système \(e.osState) · \(e.actor)")
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Localisation (LOC-01)")
        .sheet(isPresented: $showPrePrompt) { PrePromptView(module: module, isPresented: $showPrePrompt) }
        .confirmationDialog("Supprimer les relevés de localisation ?", isPresented: $confirmDelete, titleVisibility: .visible) {
            Button("Supprimer \(module.samples.count) relevés", role: .destructive) { module.deleteAllSamples() }
            Button("Annuler", role: .cancel) {}
        } message: {
            Text("Efface tous les relevés de position gardés en mémoire par l'application. Le journal des commandes (sans coordonnées) est conservé jusqu'à la fermeture de l'application. Aucun export n'existe : rien d'autre à rappeler.")
        }
    }

    private func row(_ k: String, _ v: String) -> some View {
        HStack { Text(k); Spacer(); Text(v).foregroundStyle(.secondary).multilineTextAlignment(.trailing) }
    }
}

struct PrePromptView: View {
    let module: LocationModule
    @Binding var isPresented: Bool

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    item("Ce qui est collecté", "La position que votre iPhone rapporte, au plus un relevé toutes les 5 secondes environ, ainsi que l'heure de chaque relevé. Le niveau de précision accordé par iOS (précis ou approximatif) est noté tel quel.")
                    item("Ce qui ne l'est pas", "Les noms de lieux, vos contacts, la position d'autres personnes. Aucune conclusion n'est tirée d'une absence de relevé.")
                    item("Mode d'utilisation", "Seulement quand l'application est ouverte et affichée. Aucun relevé en arrière-plan ni écran verrouillé dans cette version.")
                    item("Où c'est stocké", "En mémoire sur ce téléphone seulement, et perdu à la fermeture de l'application. Rien n'est exporté ni envoyé. (Version d'essai : le stockage protégé n'est pas encore décidé.)")
                    item("Comment arrêter", "Bouton Pause dans l'application, ou désactivation dans Réglages > Confidentialité et sécurité > Service de localisation.")
                    item("Effet de la suppression", "Les relevés de position gardés par l'application sont effacés.")
                    Text("Choisir « Continuer » affichera une question d'autorisation d'iOS.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Button("Continuer vers la demande du système") {
                        isPresented = false
                        module.enableAfterPrePrompt()
                    }
                    .buttonStyle(.borderedProminent)
                    Button("Pas maintenant") {
                        isPresented = false
                        module.declinePrePrompt()
                    }
                    .buttonStyle(.bordered)
                }
                .padding()
            }
            .navigationTitle("Localisation")
            .navigationBarTitleDisplayMode(.inline)
            .interactiveDismissDisabled()
        }
    }

    private func item(_ title: String, _ body: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title).font(.headline)
            Text(body)
        }
    }
}
