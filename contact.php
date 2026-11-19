<?php
// Xserver PHP endpoint. Never store inquiry contents on disk or in logs.
declare(strict_types=1);
ini_set('display_errors', '0');
header('Content-Type: application/json; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Robots-Tag: noindex');

function respond(int $status, array $body): void {
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_UNICODE);
    exit;
}
function fail(int $status, string $message): void {
    respond($status, ['ok' => false, 'message' => $message]);
}
set_exception_handler(function (Throwable $error): void {
    fail(503, '送信サービスを利用できません。時間をおいてお試しください。');
});

$method = $_SERVER['REQUEST_METHOD'] ?? '';
if (!in_array($method, ['GET', 'POST'], true)) {
    header('Allow: GET, POST');
    fail(405, 'この操作には対応していません。');
}
if (isset($_SERVER['HTTP_ORIGIN']) && $_SERVER['HTTP_ORIGIN'] !== 'https://miraiz.sofi-school.com') {
    fail(403, '公式サイトから送信してください。');
}
if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 32768) {
    fail(413, '入力内容が長すぎます。短くしてお試しください。');
}
session_name('miraiz_contact');
session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off', 'httponly' => true, 'samesite' => 'Strict']);
if (!session_start()) {
    fail(503, '送信サービスを利用できません。時間をおいてお試しください。');
}
if (empty($_SESSION['csrf'])) {
    $_SESSION['csrf'] = bin2hex(random_bytes(32));
}
if ($method === 'GET') {
    respond(200, ['ok' => true, 'token' => $_SESSION['csrf']]);
}
if (!is_string($_POST['token'] ?? null) || !hash_equals($_SESSION['csrf'], $_POST['token'])) {
    fail(403, '送信画面の有効期限が切れました。もう一度送信してください。');
}

function field(string $key, int $limit, bool $required = false): string {
    $value = $_POST[$key] ?? '';
    if (!is_string($value) || !preg_match('//u', $value) || strlen($value) > $limit || strpos($value, "\0") !== false) {
        fail(422, '入力内容の形式や文字数をご確認ください。');
    }
    $value = trim($value);
    if ($required && $value === '') {
        fail(422, '必須項目を入力してください。');
    }
    return $value;
}
if (field('website', 500) !== '') {
    fail(422, '送信できませんでした。入力内容をご確認ください。');
}
$name = field('name', 300, true);
$role = field('role', 100, true);
$grade = field('grade', 100);
$tel = field('tel', 50, true);
$email = field('email', 254);
$message = field('message', 15000);
$agree = field('agree', 10, true);
$purposes = $_POST['purpose'] ?? [];
$allowedPurposes = ['見学したい', '体験したい', '資料が欲しい', 'まず相談したい'];
$allowedGrades = ['', '小学1年', '小学2年', '小学3年', '小学4年', '小学5年', '小学6年', '中学1年', '中学2年', '中学3年', 'その他'];
if (!in_array($role, ['保護者', '本人', '学校・支援機関の方', 'その他'], true)
    || !in_array($grade, $allowedGrades, true) || $agree !== 'on'
    || !preg_match('/\A[0-9０-９+＋()（） 　\-ー−]{6,50}\z/u', $tel)
    || ($email !== '' && (!filter_var($email, FILTER_VALIDATE_EMAIL) || preg_match('/[\r\n]/', $email)))
    || !is_array($purposes) || count($purposes) < 1 || count($purposes) > 4) {
    fail(422, 'ご記入者・電話番号・メールアドレス・ご希望の内容・同意をご確認ください。');
}
foreach ($purposes as $purpose) {
    if (!in_array($purpose, $allowedPurposes, true)) {
        fail(422, 'ご希望の内容を選択してください。');
    }
}
// Same payload can be retried safely when the browser loses the response.
$digest = hash('sha256', json_encode([$name, $role, $grade, $tel, $email, $message, $purposes]));
if (isset($_SESSION['sent'][$digest]) && $_SESSION['sent'][$digest] > time() - 3600) {
    respond(200, ['ok' => true]);
}

// Shared per-IP throttling, outside the document root; no forwarded headers trusted.
$rateDir = sys_get_temp_dir() . '/miraiz-contact-rate';
if (!is_dir($rateDir) && !@mkdir($rateDir, 0700, true) && !is_dir($rateDir)) {
    fail(503, '送信サービスを利用できません。時間をおいてお試しください。');
}
// Fixed buckets bound disk use without retaining IP addresses.
$bucket = substr(hash('sha256', $_SERVER['REMOTE_ADDR'] ?? 'unknown'), 0, 3);
$lock = fopen($rateDir . '/' . $bucket, 'c+');
if (!$lock || !flock($lock, LOCK_EX)) {
    fail(503, '送信サービスを利用できません。時間をおいてお試しください。');
}
$attempts = json_decode(stream_get_contents($lock), true);
$attempts = is_array($attempts) ? array_values(array_filter($attempts, function ($t) { return is_int($t) && $t > time() - 3600; })) : [];
if (count($attempts) >= 5) {
    header('Retry-After: 3600');
    fail(429, '短時間に送信が続いています。1時間ほどおいてお試しいただくか、お電話でお問い合わせください。');
}
$attempts[] = time();
rewind($lock);
ftruncate($lock, 0);
fwrite($lock, json_encode($attempts));
fflush($lock);
flock($lock, LOCK_UN);
fclose($lock);

$recipient = 'contact@sofi-school.com';
$subject = '=?UTF-8?B?' . base64_encode('【MIRAIZ阪急塚口校】お問い合わせ') . '?=';
$body = "MIRAIZ阪急塚口校の公式サイトからお問い合わせが届きました。\n\n"
    . "お名前：{$name}\nご記入者：{$role}\n学年：{$grade}\n電話番号：{$tel}\nメールアドレス：{$email}\n"
    . 'ご希望の内容：' . implode('、', array_unique($purposes))
    . "\n\nご相談内容：\n{$message}\n\n個人情報の取り扱い：同意済み\n";
$headers = [
    'From: MIRAIZ <contact@sofi-school.com>',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: base64',
];
if ($email !== '') {
    $headers[] = 'Reply-To: ' . $email;
}
if (!mail($recipient, $subject, chunk_split(base64_encode($body)), implode("\r\n", $headers), '-fcontact@sofi-school.com')) {
    fail(503, '送信できませんでした。時間をおいてお試しいただくか、06-6415-6977 までお電話ください。');
}
$_SESSION['sent'] = array_filter($_SESSION['sent'] ?? [], function ($t) { return $t > time() - 3600; });
$_SESSION['sent'][$digest] = time();
respond(200, ['ok' => true]);
