import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import api, { apiErrorMessage } from '../services/api';

const COPY = {
  en: {
    title: 'Report a Public Issue',
    intro: 'Photographs and GPS are stored in NEXUS AI. This form does not send the report to Janaspandana, Panchatantra, or Panchamitra.',
    description: 'Description',
    category: 'Category',
    photo: 'Photograph',
    video: 'Short video',
    gps: 'Use this device GPS',
    district: 'District, as you know it',
    taluk: 'Taluk, as you know it',
    village: 'Village, as you know it',
    gp: 'Gram Panchayat, as you know it',
    citizenNote: 'These names are what you entered. They are not treated as a verified boundary.',
    consent: 'Keep status updates in my NEXUS AI account.',
    submit: 'Submit report',
    camera: 'Open GPS Camera',
  },
  kn: {
    title: 'ಸಾರ್ವಜನಿಕ ಸಮಸ್ಯೆಯನ್ನು ವರದಿ ಮಾಡಿ',
    intro: 'ಫೋಟೋ ಮತ್ತು GPS ಮಾಹಿತಿ NEXUS AI ನಲ್ಲಿ ಉಳಿಯುತ್ತದೆ. ಈ ಅರ್ಜಿ ಜನಸ್ಪಂದನ, ಪಂಚತಂತ್ರ ಅಥವಾ ಪಂಚಮಿತ್ರಕ್ಕೆ ಕಳುಹಿಸುವುದಿಲ್ಲ.',
    description: 'ವಿವರಣೆ',
    category: 'ವರ್ಗ',
    photo: 'ಛಾಯಾಚಿತ್ರ',
    video: 'ಕಿರು ವೀಡಿಯೊ',
    gps: 'ಈ ಸಾಧನದ GPS ಬಳಸಿ',
    district: 'ನಿಮಗೆ ತಿಳಿದ ಜಿಲ್ಲೆ',
    taluk: 'ನಿಮಗೆ ತಿಳಿದ ತಾಲೂಕು',
    village: 'ನಿಮಗೆ ತಿಳಿದ ಗ್ರಾಮ',
    gp: 'ನಿಮಗೆ ತಿಳಿದ ಗ್ರಾಮ ಪಂಚಾಯಿತಿ',
    citizenNote: 'ಈ ಹೆಸರುಗಳನ್ನು ನೀವು ನಮೂದಿಸಿದ್ದೀರಿ. ಅವು ಪರಿಶೀಲಿತ ಗಡಿ ಎಂದು ಪರಿಗಣಿಸುವುದಿಲ್ಲ.',
    consent: 'ಸ್ಥಿತಿ ನವೀಕರಣಗಳನ್ನು ನನ್ನ NEXUS AI ಖಾತೆಯಲ್ಲಿ ಇಡಿ.',
    submit: 'ವರದಿ ಸಲ್ಲಿಸಿ',
    camera: 'GPS ಕ್ಯಾಮೆರಾ ತೆರೆಯಿರಿ',
  },
} as const;

const CATEGORIES = [
  'Damaged roads and potholes',
  'Garbage accumulation',
  'Drainage and sewage problems',
  'Drinking water problems',
  'Broken streetlights',
  'Public sanitation',
  'Flooding and waterlogging',
  'Damaged public infrastructure',
  'Public building maintenance',
  'Other civic issues',
];

export default function PublicIssue() {
  const [lang, setLang] = useState<'en' | 'kn'>('en');
  const text = COPY[lang];
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [photo, setPhoto] = useState<File | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [coords, setCoords] = useState<{ latitude: number; longitude: number; accuracy: number } | null>(null);
  const [gpsNote, setGpsNote] = useState('');
  const [district, setDistrict] = useState('');
  const [taluk, setTaluk] = useState('');
  const [village, setVillage] = useState('');
  const [gp, setGp] = useState('');
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const locate = () => {
    if (!navigator.geolocation) {
      setGpsNote(lang === 'kn' ? 'ಈ ಬ್ರೌಸರ್ GPS ನೀಡುವುದಿಲ್ಲ.' : 'This browser does not provide GPS.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
        setGpsNote('');
      },
      () => {
        setCoords(null);
        setGpsNote(lang === 'kn'
          ? 'ಸ್ಥಳ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ನಕ್ಷೆ ಸ್ಥಾನವನ್ನು ಊಹಿಸಲಾಗಿಲ್ಲ.'
          : 'Location permission was denied. No position was assumed.');
      },
      { enableHighAccuracy: true, timeout: 12000 },
    );
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    const form = new FormData();
    form.append('description', description);
    form.append('category', category);
    form.append('notify_consent', consent ? 'true' : 'false');
    if (coords) {
      form.append('latitude', String(coords.latitude));
      form.append('longitude', String(coords.longitude));
      form.append('gps_accuracy', String(coords.accuracy));
    }
    if (district) form.append('citizen_district', district);
    if (taluk) form.append('citizen_taluk', taluk);
    if (village) form.append('citizen_village', village);
    if (gp) form.append('citizen_gram_panchayat', gp);
    if (photo) form.append('photo', photo);
    if (video) form.append('video', video);
    try {
      const response = await api.post('/civic/reports', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(response.data);
    } catch (err) {
      setError(apiErrorMessage(err, 'The report was not saved.'));
    }
  };

  const verified = (result?.verified_jurisdiction || {}) as Record<string, string>;
  const ai = (result?.ai || {}) as Record<string, string | number | null>;

  return (
    <AppLayout>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Karnataka</p>
          <h1 className="mt-1 text-2xl font-semibold text-white">{text.title}</h1>
        </div>
        <button type="button" onClick={() => setLang(lang === 'en' ? 'kn' : 'en')} className="rounded-xl border border-slate-700 px-3 py-2 text-sm">
          {lang === 'en' ? 'ಕನ್ನಡ' : 'English'}
        </button>
      </div>
      <p className="text-sm leading-relaxed text-slate-400">{text.intro}</p>
      <Link to="/gps-camera" className="text-sm text-cyan-200">{text.camera}</Link>
      <form onSubmit={submit} className="space-y-4 rounded-3xl border border-slate-800 bg-slate-900/70 p-4">
        <label className="block text-sm">{text.description}
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} required minLength={10} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2" />
        </label>
        <label className="block text-sm">{text.category}
          <select value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2">
            {CATEGORIES.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="block text-sm">{text.photo}
          <input type="file" accept="image/jpeg,image/png,image/webp" className="mt-1 block w-full text-sm" onChange={(event) => setPhoto(event.target.files?.[0] || null)} />
        </label>
        <label className="block text-sm">{text.video}
          <input type="file" accept="video/mp4,video/webm" className="mt-1 block w-full text-sm" onChange={(event) => setVideo(event.target.files?.[0] || null)} />
        </label>
        <button type="button" onClick={locate} className="rounded-xl border border-slate-700 px-3 py-2 text-sm">{text.gps}</button>
        {coords && <p className="text-sm text-slate-300">{coords.latitude.toFixed(5)}, {coords.longitude.toFixed(5)} · {Math.round(coords.accuracy)} m</p>}
        {gpsNote && <p className="text-sm text-amber-100">{gpsNote}</p>}
        <div className="grid gap-3 sm:grid-cols-2">
          <input value={district} onChange={(event) => setDistrict(event.target.value)} placeholder={text.district} className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
          <input value={taluk} onChange={(event) => setTaluk(event.target.value)} placeholder={text.taluk} className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
          <input value={village} onChange={(event) => setVillage(event.target.value)} placeholder={text.village} className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
          <input value={gp} onChange={(event) => setGp(event.target.value)} placeholder={text.gp} className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm" />
        </div>
        <p className="text-xs text-slate-500">{text.citizenNote}</p>
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1" />{text.consent}</label>
        {error && <p className="text-sm text-rose-200" role="alert">{error}</p>}
        <button className="rounded-xl bg-cyan-300 px-4 py-2 text-sm font-semibold text-slate-950">{text.submit}</button>
      </form>
      {result && (
        <section className="rounded-2xl border border-slate-800 p-4 text-sm">
          <h2 className="text-lg font-semibold text-white">NEXUS AI {String(result.reference)}</h2>
          <p className="mt-2">Status: {String(result.status)}</p>
          <p>Jurisdiction: {verified.status}. Verified Gram Panchayat: {verified.gram_panchayat || 'Pending verification'}</p>
          <p>Government delivery: {String(result.government_delivery)}</p>
          <p>AI status: {String(ai.status)}. Severity: {ai.severity ? String(ai.severity) : 'not estimated'}. {String(ai.risk_note || '')}</p>
          <Link to="/my-reports" className="mt-3 inline-block text-cyan-200">View your reports</Link>
        </section>
      )}
    </AppLayout>
  );
}
