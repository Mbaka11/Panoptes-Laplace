import SwiftUI

/// MOT-01 screens: pre-prompt (before any Core Motion call), two state layers, controls,
/// resume/backfill choice, history import report, counts and control log.
/// French texts follow docs/participant-text-fr.md section 2.2.
struct MotionView: View {
    @Bindable var module: MotionModule
    @State private var prePrompt: PromptMode?
    @State private var confirmDelete = false
    @State private var askResume = false

    enum PromptMode: Identifiable { case live, importHistory; var id: Int { self == .live ? 0 : 1 } }

    private static let df: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd HH:mm xxx"; return f
    }()
    private static let tf: DateFormatter = {
        let f = DateFormatter(); f.dateFormat = "HH:mm:ss"; return f
    }()
    private func fmt(_ d: Date?) -> String { d.map { Self.df.string(from: $0) } ?? "aucun" }

    var body: some View {
        List {
            Section {
                Text("VERSION D'ESSAI : non approuvée pour des données réelles. Les enregistrements restent en mémoire sur ce téléphone seulement, sont perdus à la fermeture de l'application, et ne sont ni exportés ni transmis.")
                    .font(.footnote).foregroundStyle(.orange)
            }
            Section("États (deux couches distinctes)") {
                row("État de la sonde", module.probeState.rawValue)
                row("État du système (iOS)", module.osLabel)
                row("Disponibilité", module.availabilityLabel)
                row("Observé à", module.osObservedAt.map { Self.tf.string(from: $0) } ?? "jamais")
                row("Collecte en direct en cours", module.isCollecting ? "oui" : "non")
                if module.probeState == .blockedByOS {
                    Text("Bloqué par le système : modifiez l'autorisation dans Réglages > Confidentialité et sécurité > Mouvements et forme > Sensor Probe. L'application ne redemandera pas en boucle.")
                        .font(.footnote)
                }
            }
            Section("Commandes") {
                switch module.probeState {
                case .off:
                    Button("Activer le mouvement (en direct)…") { module.logExplained(); prePrompt = .live }
                case .on:
                    Button("Pause") { module.pause() }
                case .paused:
                    Button("Reprendre…") { askResume = true }
                case .blockedByOS:
                    Button("Réessayer l'explication") { module.logExplained(); prePrompt = .live }
                }
                Button("Importer l'historique conservé par iOS…") { module.logExplained(); prePrompt = .importHistory }
                Button("Supprimer les enregistrements…", role: .destructive) { confirmDelete = true }
                    .disabled(!module.hasRecords && module.imports.isEmpty)
            }
            Section("Activité (intervalles) : appareil, pas comportement observé") {
                row("Segments", "\(module.segments.count)")
                row("dont en direct / historique / rattrapage", "\(module.count(.live)) / \(module.count(.historyImport)) / \(module.count(.backfillAfterPause))")
                row("Premier début / dernier début", "\(fmt(module.oldestSegment)) / \(fmt(module.latestSegment))")
                let c = module.confidenceCounts
                row("Confiance faible / moyenne / haute", "\(c.low) / \(c.medium) / \(c.high)")
                row("Étiquettes « unknown » (aucune estimation)", "\(module.unknownLabelCount)")
                row("Jours couverts par l'historique importé", "\(module.activityDaysCovered)")
                row("Doublons écartés", "\(module.duplicatesDropped)")
            }
            Section("Podomètre (agrégats sur une fenêtre)") {
                row("Fenêtres historiques / en direct / rattrapage", "\(module.windows(.historyImport)) / \(module.windows(.live)) / \(module.windows(.backfillAfterPause))")
                row("Pas (fenêtres historiques et rattrapage)", "\(module.totalSteps)")
                row("Pas cumulés en direct (séances)", "\(module.liveSteps)")
                row("Séances en direct", "\(module.runCount)")
                row("Pauses volontaires", "\(module.pausedIntervals.count)")
                row("Erreurs Core Motion (codes)", module.errorCodes.isEmpty ? "aucune" : module.errorCodes.map(String.init).joined(separator: ", "))
                Text("Un résultat vide ou à zéro ne prouve ni refus d'accès, ni absence de mouvement, ni absence d'historique. Seule l'heure du premier segment renvoyé indique la profondeur réellement obtenue. Tant que l'écran n'est pas affiché, aucune mise à jour en direct n'est prise.")
                    .font(.footnote).foregroundStyle(.secondary)
            }
            Section("Importations d'historique (fenêtre demandée et renvoyée)") {
                if module.imports.isEmpty { Text("aucune").foregroundStyle(.secondary) }
                ForEach(module.imports.reversed()) { r in
                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(Self.tf.string(from: r.at))  \(r.kind.rawValue)\(r.pending > 0 ? " (en cours)" : "")").font(.callout)
                        Text("demandé \(fmt(r.requestedFrom)) → \(fmt(r.requestedTo))").font(.caption2)
                        Text("activité : \(r.activityReturned) renvoyés (\(r.activityAdded) ajoutés) ; premier \(fmt(r.oldestActivity)) ; dernier \(fmt(r.latestActivity))").font(.caption2)
                        Text("podomètre : \(r.pedometerWindowsReturned)/\(r.pedometerWindowsAsked) fenêtres, \(r.pedometerDaysWithSteps) avec des pas ; erreurs : \(r.errors.isEmpty ? "aucune" : r.errors.map(String.init).joined(separator: ", "))").font(.caption2)
                    }.foregroundStyle(.secondary)
                }
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
        .navigationTitle("Mouvement (MOT-01)")
        .sheet(item: $prePrompt) { mode in MotionPrePromptView(module: module, mode: mode, dismiss: { prePrompt = nil }) }
        .confirmationDialog("Reprendre le mouvement", isPresented: $askResume, titleVisibility: .visible) {
            Button("Reprendre à partir de maintenant, sans importer (par défaut)") { module.resume(importPausedInterval: false) }
            Button("Reprendre et aussi importer la période en pause (marquée « rattrapage »)") { module.resume(importPausedInterval: true) }
            Button("Annuler", role: .cancel) {}
        } message: {
            Text("Pendant la pause, iOS a pu continuer à garder l'historique de mouvement. Voulez-vous aussi récupérer cette période ? Les enregistrements importés seront étiquetés « rattrapage après pause » pour ne pas être confondus avec une observation en direct.")
        }
        .confirmationDialog("Supprimer les enregistrements de mouvement ?", isPresented: $confirmDelete, titleVisibility: .visible) {
            Button("Supprimer \(module.recordCount) enregistrements", role: .destructive) { module.deleteAll() }
            Button("Annuler", role: .cancel) {}
        } message: {
            Text("Efface tout ce que l'application garde en mémoire pour le mouvement. L'historique conservé par iOS lui-même n'est pas supprimé par l'application. Le journal des commandes (sans valeurs) est conservé jusqu'à la fermeture. Aucun export n'existe.")
        }
    }

    private func row(_ k: String, _ v: String) -> some View {
        HStack { Text(k); Spacer(); Text(v).foregroundStyle(.secondary).multilineTextAlignment(.trailing) }
    }
}

struct MotionPrePromptView: View {
    let module: MotionModule
    let mode: MotionView.PromptMode
    let dismiss: () -> Void

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    item("Ce qui est collecté", "Les types de mouvement que l'iPhone a déjà détectés (marche, course, vélo, immobile, en véhicule), avec le niveau de confiance fourni par iOS, et le nombre de pas par fenêtre de temps (distance si disponible). Trois fonctions séparées : historique conservé par iOS, mises à jour en direct, podomètre.")
                    item("Ce qui ne l'est pas", "Les données brutes de l'accéléromètre et votre position. Les étiquettes viennent de l'appareil : elles ne prouvent pas ce que vous faisiez.")
                    item("Profondeur de l'historique", "iOS garde un historique limité (la documentation indique 7 jours). L'écran affichera la période réellement renvoyée, jamais une période supposée, et le dira si rien n'est renvoyé.")
                    if mode == .importHistory {
                        item("Cette action", "Lit une fois l'historique que iOS conserve pour cette application, à votre demande. Elle n'active pas la collecte en direct.")
                    } else {
                        item("Mode d'utilisation", "Mises à jour en direct seulement quand l'application est ouverte et affichée. Rien en arrière-plan ni écran verrouillé dans cette version.")
                    }
                    item("Où c'est stocké", "En mémoire sur ce téléphone seulement, perdu à la fermeture de l'application. Rien n'est exporté ni envoyé. (Version d'essai : le stockage protégé n'est pas encore décidé.)")
                    item("Comment arrêter", "Bouton Pause dans l'application, ou désactivation dans Réglages > Confidentialité et sécurité > Mouvements et forme. À la reprise, vous choisirez séparément si la période en pause est récupérée (par défaut : non).")
                    item("Effet de la suppression", "Les enregistrements gardés par l'application sont effacés. L'historique conservé par iOS lui-même n'est pas supprimé par l'application.")
                    Text("Choisir « Continuer » peut afficher une question d'autorisation d'iOS.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Button("Continuer vers la demande du système") {
                        dismiss()
                        if mode == .live { module.enableAfterPrePrompt() } else { module.importHistoryAfterPrePrompt() }
                    }
                    .buttonStyle(.borderedProminent)
                    Button("Pas maintenant") {
                        dismiss()
                        module.declinePrePrompt()
                    }
                    .buttonStyle(.bordered)
                }
                .padding()
            }
            .navigationTitle("Mouvement")
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
