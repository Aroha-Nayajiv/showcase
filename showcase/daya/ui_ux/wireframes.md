# Donor Onboarding & Funding Activation

This artifact defines the secure, PCI-DSS Level 1 compliant onboarding flow for the Donor ([ACT-80C62C7814](../project_glossary.md#act-80c62c7814)) within the MealCredit platform. The primary objective is to facilitate the [JNY-62D850E94B](../project_glossary.md#jny-62d850e94b) journey by securely linking funding sources and establishing initial KYC/AML verification states without ever capturing raw card data on client-side infrastructure.

### 1.1 Security & Compliance Architecture

To strictly adhere to PCI-DSS Level 1 compliance ([CON-66390130AA](../project_glossary.md#con-66390130aa)) and SOC2 Type II structural planning ([CON-81FB01F06B](../project_glossary.md#con-81fb01f06b)), the UI implementation relies entirely on hosted fields and iframes provided by Stripe Elements.

Data Isolation: No raw card numbers, CVVs, or expiration dates are ever rendered in the React Native component tree or stored in local state.
Tokenization: All financial interactions are routed through Stripe's secure environment, returning only ephemeral tokens to the MealCredit API orchestration layer.
KYC/AML Integration: Identity verification is handled via Plaid Link, ensuring that sensitive PII is transmitted directly to the financial data provider, maintaining strict data isolation where beneficiary demographic status and legal names are cryptographically segregated from public donor views ([CON-0A0288EED4](../project_glossary.md#con-0a0288eed4)).

### 1.2 Onboarding Flow States

The Donor Onboarding & Funding Activation journey (JNY-62D850E94B) is structured into three distinct, progressive disclosure states to minimize cognitive load and maximize completion rates.

#### State 1: Identity & Initial Verification
Action: Donor (ACT-80C62C7814) enters basic contact information (Email, Phone).
Validation: Real-time format validation with accessible error messages (WCAG 2.1 AA compliant).
Transition: Triggers the Plaid Link modal for identity verification.
Loading State: Displays a skeleton loader with a clear progress indicator, ensuring the interface remains responsive and accessible.

#### State 2: Funding Source Activation
Action: Donor links a funding source (Credit/Debit Card or Bank Account) via Stripe Elements.
UI Component: A secure, iframe-embedded form that matches the platform's high-contrast design system ([CON-68497304B1](../project_glossary.md#con-68497304b1)).
Feedback: Real-time validation feedback (e.g., "Card type detected: Visa") without exposing sensitive data.
Error Handling: Clear, actionable error messages for declined cards or invalid details, with a retry mechanism that preserves entered data.

#### State 3: Confirmation & Impact Preview
Action: Upon successful funding activation, the Donor is presented with a confirmation screen.
Content: Summary of the linked funding source (masked, e.g., `•••• 4242`) and an initial preview of the 'Impact Stream' (see sibling artifact for full visualization details).
Transition: Redirects to the Donor Dashboard or the Donation Preference Configuration flow.

### 1.3 Accessibility & Inclusivity

The onboarding interface is designed to be fully accessible to visually impaired donors, ensuring compliance with WCAG 2.1 AA standards (CON-68497304B1).

Screen Reader Support: All form inputs have associated, descriptive labels. Error messages are announced immediately via ARIA live regions.
High-Contrast Mode: The UI supports system-level high-contrast modes, ensuring all interactive elements and text remain legible.
Keyboard Navigation: All interactive elements are focusable and navigable via standard keyboard controls, with visible focus indicators.

## 2. Donation Preference Configuration

This artifact defines the high-fidelity user interface and interaction flows for the Donor (ACT-80C62C7814) to configure their financial impact preferences within the MealCredit platform. The interface is designed to translate complex financial decisions—round-ups, directed impact, and open pool allocation—into an intuitive, accessible, and visually hierarchical experience.

### 2.1 Architectural Surface & Component Hierarchy

The configuration interface is a dedicated screen within the Donor module, accessible after the initial funding activation (JNY-62D850E94B). It leverages the platform's event-driven architecture to provide real-time feedback on donation velocity.

 Component: DonationPreferenceWizard
  Purpose: Orchestrates the multi-step configuration flow.
  Props: donorId, initialFundingStatus, onPreferenceSave.
  States: idle, roundup_config, impact_selection, pool_allocation, confirmation.

 Component: RoundUpToggleGroup
  Purpose: Allows donors to configure transaction round-ups for their linked payment methods.
  Controls: Toggle switches for each enabled payment method (e.g., Visa ending in 1234).
  Input: Numeric field for round-up amount (e.g., $0.50, $1.00, $2.00).
  Visual Feedback: Real-time estimated monthly impact display.

 Component: ImpactSelector
  Purpose: Enables directed impact selection.
  Options:
  Open Pool: Default allocation to the general MealCredit fund.
  Directed Impact: Select specific NGOs or metropolitan regions (SF, NYC, Chicago).
  Data Source: Fetches available NGOs and regions via GraphQL query.

 Component: PoolAllocationSlider
  Purpose: Distributes donation volume between Open Pool and Directed Impact.
  Interaction: Horizontal slider with two endpoints.
  Validation: Sum of allocations must equal 100%.

### 2.2 Interaction Flow & Visual Hierarchy

The flow is designed to minimize cognitive load while ensuring informed decision-making.

1. Step 1: Round-Up Configuration
  Action: Donor selects payment methods and sets round-up amounts.
  Feedback: A dynamic "Estimated Monthly Impact" counter updates in real-time, showing the projected number of meals funded.
  Accessibility: All toggles and inputs must have associated aria-label attributes. Color is not the sole indicator of state.

2. Step 2: Impact Selection
  Action: Donor chooses between Open Pool and Directed Impact.
  Directed Impact Detail: If "Directed Impact" is selected, a searchable list of NGO Operators ([ACT-09E028AEB0](../project_glossary.md#act-09e028aeb0)) and regions appears.
  Visual Hierarchy: The "Open Pool" option is presented as the default, with "Directed Impact" as a secondary, expandable option to prevent decision paralysis.

3. Step 3: Pool Allocation
  Action: Donor adjusts the slider to define the percentage of donations going to Open Pool vs. Directed Impact.
  Validation: The UI prevents saving if the slider does not sum to 100%.
  Confirmation: A summary screen displays the final configuration before saving.

### 2.3 Error Handling & Edge Cases

 Network Failure: If the GraphQL query for NGOs fails, a user-friendly error message is displayed with a "Retry" button.
 Invalid Allocation: If the donor attempts to save with an invalid pool allocation (e.g., 110% to Open Pool), inline validation errors are shown immediately.
 Insufficient Funding: If the donor's linked payment method fails during the initial funding activation, the preference configuration screen is disabled with a clear call-to-action to update payment details.

### 2.4 Deliverable: React Native Component Structure

tsx
import useState
import useEffect
import View
import Text
import Switch
import TextInput
import Slider
import TouchableOpacity
import Alert
import useDonorPreferences
import useNGOs

// Placeholder for design system tokens
const styles = {
 container: { padding: 20, backgroundColor: '#FFFFFF' },
 section: { marginBottom: 24 },
 label: { fontSize: 16, fontWeight: '600', marginBottom: 8 },
 input: { borderWidth: 1, borderColor: '#CCCCCC', padding: 10, borderRadius: 5, marginBottom: 10 },
 toggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
 impactOption: { padding: 15, borderWidth: 1, borderColor: '#CCCCCC', borderRadius: 5, marginBottom: 10 },
 selectedImpact: { borderColor: '#007AFF', backgroundColor: '#F0F8FF' },
 button: { backgroundColor: '#007AFF', padding: 15, borderRadius: 5, alignItems: 'center' },
 buttonText: { color: '#FFFFFF', fontWeight: '600', fontSize: 16 },
 error: { color: '#FF3B30', fontSize: 12, marginBottom: 10 },
};

export const DonationPreferenceConfiguration = ({ donorId, onComplete }) => {
 const { preferences, updatePreferences, loading: preferencesLoading } = useDonorPreferences(donorId);
 const { NGOs, loading: NGOsLoading } = useNGOs();

 const [roundUpAmount, setRoundUpAmount] = useState(0.50);
 const [isRoundUpEnabled, setIsRoundUpEnabled] = useState(false);
 const [selectedImpact, setSelectedImpact] = useState('OPEN_POOL');
 const [selectedNGO, setSelectedNGO] = useState(null);
 const [openPoolPercentage, setOpenPoolPercentage] = useState(100);
 const [directedImpactPercentage, setDirectedImpactPercentage] = useState(0);
 const [error, setError] = useState(null);

 useEffect(() => {
 if (preferences) {
 setRoundUpAmount(preferences.roundUpAmount || 0.50);
 setIsRoundUpEnabled(preferences.isRoundUpEnabled || false);
 setSelectedImpact(preferences.selectedImpact || 'OPEN_POOL');
 setOpenPoolPercentage(preferences.openPoolPercentage || 100);
 setDirectedImpactPercentage(preferences.directedImpactPercentage || 0);
 }
 }, [preferences]);

 const handleSave = async () => {
 if (openPoolPercentage + directedImpactPercentage !== 100) {
 setError('Total allocation must equal 100%.');
 return;
 }
 if (selectedImpact === 'DIRECTED' && !selectedNGO) {
 setError('Please select an NGO for directed impact.');
 return;
 }

 try {
 await updatePreferences({
 roundUpAmount,
 isRoundUpEnabled,
 selectedImpact,
 selectedNGO,
 openPoolPercentage,
 directedImpactPercentage,
 });
 onComplete();
 } catch (err) {
 setError('Failed to save preferences. Please try again.');
 }
 };

 if (preferencesLoading || NGOsLoading) {
 return <Text>Loading...</Text>;
 }

 return (
 <View style={styles.container}>
 <Text style={styles.label}>Round-Up Configuration</Text>
 <View style={styles.toggleRow}>
 <Text>Enable Round-Ups</Text>
 <Switch
 value={isRoundUpEnabled}
 onValueChange={setIsRoundUpEnabled}
 accessibilityLabel="Toggle round-up configuration"
 />
 </View>
 {isRoundUpEnabled && (
 <>
 <Text style={styles.label}>Round-Up Amount ($)</Text>
 <TextInput
 style={styles.input}
 keyboardType="decimal-pad"
 value={roundUpAmount.toString()}
 onChangeText={(text) => setRoundUpAmount(parseFloat(text) || 0)}
 accessibilityLabel="Round-up amount input"
 accessibilityHint="Enter the amount to round up to for each transaction"
 />
 <Text>Estimated Monthly Impact: {Math.round(roundUpAmount * 10)} meals</Text>
 </>
 )}

 <Text style={styles.label}>Impact Selection</Text>
 <TouchableOpacity
 style={[styles.impactOption, selectedImpact === 'OPEN_POOL' && styles.selectedImpact]}
 onPress={() => setSelectedImpact('OPEN_POOL')}
 accessibilityLabel="Select open pool impact"
 >
 <Text>Open Pool (General Fund)</Text>
 </TouchableOpacity>
 <TouchableOpacity
 style={[styles.impactOption, selectedImpact === 'DIRECTED' && styles.selectedImpact]}
 onPress={() => setSelectedImpact('DIRECTED')}
 accessibilityLabel="Select directed impact"
 >
 <Text>Directed Impact</Text>
 </TouchableOpacity>

 {selectedImpact === 'DIRECTED' && (
 <View>
 <Text style={styles.label}>Select NGO</Text>
 {NGOs.map((ngo) => (
 <TouchableOpacity
 key={ngo.id}
 style={[styles.impactOption, selectedNGO?.id === ngo.id && styles.selectedImpact]}
 onPress={() => setSelectedNGO(ngo)}
 accessibilityLabel={`Select NGO ${ngo.name}`}
 >
 <Text>{ngo.name}</Text>
 </TouchableOpacity>
 ))}
 </View>
 )}

 <Text style={styles.label}>Pool Allocation</Text>
 <Slider
 value={openPoolPercentage}
 onValueChange={setOpenPoolPercentage}
 onSlidingComplete={(value) => setDirectedImpactPercentage(100 - value)}
 minimumValue={0}
 maximumValue={100}
 step={1}
 accessibilityLabel="Open pool allocation slider"
 accessibilityHint="Drag to adjust the percentage of donations going to the open pool"
 />
 <Text>Open Pool: {openPoolPercentage}% | Directed Impact: {directedImpactPercentage}%</Text>

 {error && <Text style={styles.error}>{error}</Text>}

 <TouchableOpacity style={styles.button} onPress={handleSave} accessibilityLabel="Save preferences">
 <Text style={styles.buttonText}>Save Preferences</Text>
 </TouchableOpacity>
 </View>
 );
};

---

## 3. Real-Time Impact Stream Visualization

The Impact Stream is the primary donor engagement interface, designed to provide immediate, anonymous feedback on the social impact of their contributions. It visualizes the correlation between donor impact receipts and beneficiary redemption events without linking PII, strictly adhering to FTC guidelines on anonymity ([CON-B3D71A437D](../project_glossary.md#con-b3d71a437d), [CON-C22D030D21](../project_glossary.md#con-c22d030d21)) and using UUIDv4 mapping for analytics ([CON-23A501C051](../project_glossary.md#con-23a501c051), [CON-413928CB1C](../project_glossary.md#con-413928cb1c)).

### 3.1 Component Architecture & Data Flow

The Impact Stream is a React Native component (ImpactStream.tsx) that consumes real-time events via Server-Sent Events (SSE) from the Next.js Edge runtime. It does not handle raw financial data; it only receives anonymized event payloads.

 Data Source: ImpactEventStream (SSE endpoint)
 Payload Structure: `{ eventId: string, impactType: 'meal_provided' | 'nutrition_boost', timestamp: number, region: 'SF' | 'NYC' | 'CHI', anonymousId: string }`
 State Management: Local component state for the stream buffer, with a maximum of 50 visible items to prevent performance degradation on low-end devices.

### 3.2 Visual Design & Accessibility

The component uses a high-contrast, screen-reader-friendly design to ensure WCAG 2.1 AA compliance (CON-68497304B1, [CON-CD9BDF7662](../project_glossary.md#con-cd9bdf7662)).

 Visual Elements:
  Iconography: Simple, universally recognizable icons (e.g., a meal plate, a heart) to represent impact types.
  Color Palette: High-contrast colors (e.g., dark blue on white) to ensure readability for visually impaired donors.
  Animation: Subtle fade-in animations for new events to draw attention without causing distraction.
 Accessibility:
  Screen Reader Labels: Each event is wrapped in a `<Text>` component with an accessibilityLabel that describes the impact (e.g., "A meal was provided in San Francisco at 10:30 AM").
  Focus Management: New events are automatically brought into focus for screen reader users.
  High-Contrast Mode: The component respects the system's high-contrast setting, switching to a black-and-white palette if enabled.

### 3.3 Failure & Empty States

 No Events: If no events are available, the component displays a friendly message: "Your impact is growing! Check back soon for updates."
 Connection Error: If the SSE connection fails, the component displays a retry button and a message: "Unable to load impact stream. Please try again."
 Loading State: A skeleton loader is displayed while the initial stream is being fetched.

### 3.4 Implementation Notes

 Performance: The component uses FlatList with removeClippedSubviews enabled to optimize rendering performance.
 Memory Management: The component unsubscribes from the SSE stream on unmount to prevent memory leaks.
 Testing: Unit tests will verify the correct rendering of impact types and the handling of empty/error states.

This artifact's [Beneficiary Eligibility & Voucher Redemption Flow] defers to [[JNY-E82B8A88D8](../project_glossary.md#jny-e82b8a88d8)] for specific beneficiary data handling; see that artifact for the full treatment.
This artifact's [Merchant POS Integration & Dashboard] defers to [[JNY-356F465DB3](../project_glossary.md#jny-356f465db3)] for POS clearance latency details; see that artifact for the full treatment.
This artifact's [Offline Fallback & Accessibility Interface] defers to [[CON-387CDD9AEB](../project_glossary.md#con-387cdd9aeb)] for offline fallback interface design; see that artifact for the full treatment.
This artifact's [Core Design System & Token Architecture] defers to [[SUR-43E71C4E2B](../project_glossary.md#sur-43e71c4e2b)] for token definitions; see that artifact for the full treatment.

---

## 4. Offline Fallback Interface for Donor Transaction Monitoring

This artifact defines the offline-first UI/UX strategy for the Donor (ACT-80C62C7814) module, ensuring that donors can monitor their transaction status and history even when network connectivity is lost or degraded. The design prioritizes intuitive interaction paths (voice, tap, scan) and strict adherence to accessibility standards (CON-68497304B1) to maintain trust and transparency in the MealCredit platform.

### 4.1 Offline State Management & Data Persistence

The offline fallback interface relies on a local-first architecture using Expo's SecureStore ([CON-34312C6DC9](../project_glossary.md#con-34312c6dc9)) to cache critical transaction data. This ensures that donors can always view their recent donation history and impact receipts, even without an active internet connection.

Local Data Store: A local SQLite database (via expo-sqlite) will store the last 50 transactions, including timestamp, amount, impact category (if directed), and a unique transaction ID (UUIDv4).
Sync Queue: Any new donations initiated offline are queued in a local 'pending' state. Upon reconnection, the app will automatically sync these transactions with the backend via the GraphQL API.
Conflict Resolution: In the event of a sync conflict (e.g., duplicate transactions due to network retry), the backend's append-only cryptographic log ([CON-1762EA5021](../project_glossary.md#con-1762ea5021)) will serve as the source of truth. The UI will display a 'Syncing...' state and resolve conflicts transparently.

### 4.2 Intuitive Interaction Paths

To ensure accessibility and ease of use, the offline interface supports multiple interaction modalities:

Tap: Standard touch interactions for navigating the transaction history list and viewing details. All interactive elements must have a minimum touch target size of 44x44 points (iOS) / 48x48 dp (Android) to accommodate users with motor impairments.
Voice: Integration with Expo's voice recognition capabilities allows donors to query their transaction history using voice commands (e.g., "Show my last donation"). Voice commands are processed locally when possible, with fallback to cloud-based processing when online.
Scan: While primarily used for beneficiary redemption, the scan functionality is also available for donors to scan a QR code on a receipt to view detailed impact analytics. This feature is available offline if the QR code contains a locally cached UUIDv4 mapping (CON-23A501C051).

## 5. Comprehensive Accessibility (WCAG) Standards for the Donor Module

This artifact defines the mandatory accessibility standards for the Donor module (ACT-80C62C7814) within the MealCredit platform, ensuring strict compliance with WCAG 2.1 Level AA. The standards apply to the Expo mobile application (React Native/Fabric) and the associated Wallet passes, covering the Donor Onboarding & Funding Activation journey (JNY-62D850E94B).

### 5.1 Screen Reader Compatibility (Expo Mobile Application)

All interactive elements within the Donor onboarding flow must be fully operable and describable by VoiceOver (iOS) and TalkBack (Android).

 Focus Management: Focus must be programmatically managed during the multi-step onboarding wizard. When a step completes, focus must shift to the primary action button of the next step or a live region announcing the transition.
 Dynamic Announcements: Real-time updates to the 'Impact Stream' visualization must be announced via AccessibilityInfo or Announcer components. Changes in donation status or round-up configuration must trigger a concise, non-intrusive announcement (e.g., "Donation preference updated to directed impact.").
 Form Labels: All input fields in the Plaid/Stripe Elements integration (where accessible via the SDK) and custom form fields (e.g., donation amount, round-up toggle) must have explicit, descriptive accessibilityLabel and accessibilityHint props. Placeholders are not sufficient substitutes for labels.
 Error Identification: Form validation errors must be announced immediately upon submission failure. Error messages must be associated with the relevant input field using accessibilityError or by moving focus to the first error.

### 5.2 High-Contrast and Color Independence

The UI must remain fully functional and legible in high-contrast modes (iOS Dynamic Type/High Contrast, Android High Contrast Text).

 Color Independence: Color must never be the sole means of conveying information. For example, the 'Impact Stream' visualization must use distinct patterns or icons in addition to color to differentiate between 'Open Pool' and 'Directed Impact' contributions.
 Contrast Ratios: All text and interactive elements must maintain a minimum contrast ratio of 4.5:1 against their background (WCAG AA). For large text (18pt+ or 14pt+ bold), the minimum ratio is 3:1.
 Focus Indicators: All focusable elements must have a clearly visible focus indicator that is at least 2px thick and contrasts significantly with the background. The default platform focus ring must be enhanced if it does not meet this threshold.

### 5.5 Testing and Validation

 Automated Testing: Accessibility linting tools (e.g., eslint-plugin-jsx-a11y, react-native-a11y) must be integrated into the CI/CD pipeline to catch common accessibility violations early.
 Manual Testing: Manual testing with VoiceOver and TalkBack must be performed for every major user flow, including onboarding, donation configuration, and impact stream viewing.
 User Testing: Accessibility testing with users who have disabilities must be conducted at least once per major release to validate the effectiveness of the implemented standards.

### 5.6 Knowledge Gaps and Assumptions

 KNOWLEDGE_GAP: The specific implementation details for integrating Plaid/Stripe Elements with React Native's accessibility APIs are not yet defined. The design team must collaborate with the payment provider's documentation to ensure the SDKs expose necessary accessibility properties.
 ASSUMPTION: The project will use the latest stable version of Expo (v51) and React Native, which provide robust built-in accessibility support. If an older version is used, additional polyfills or custom components may be required.
 ASSUMPTION: The 'Impact Stream' visualization will be implemented using standard React Native components (e.g., View, Text, Image) rather than a custom canvas-based solution, to ensure native accessibility support. If a custom solution is required, additional accessibility workarounds will be necessary.

This artifact ensures that the Donor module is inclusive and accessible to all users, aligning with the platform's mission to decouple food assistance from social stigma and ensuring a seamless experience for donors with diverse abilities.