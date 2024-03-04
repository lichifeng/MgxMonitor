<?php
if (isset($_GET['md5'])) {
    $md5 = $_GET['md5'];
    $zip_file = "D/{$md5}.zip";

    $zip = new ZipArchive;
    if ($zip->open($zip_file) === TRUE) {
        $file_to_unzip = $zip->getNameIndex(0);  // 假设 ZIP 文件中只有一个文件
        $zip->extractTo('.', $file_to_unzip);
        $zip->close();

        // 开始捕获输出
        ob_start();

        // 读取并发送文件内容
        readfile($file_to_unzip);

        // 获取并清除输出缓冲区的内容
        $content = ob_get_clean();

        // 设置响应头
        header('Content-Encoding: gzip');
        header('Content-Length: ' . strlen($content));
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename=' . basename($file_to_unzip));

        // 发送内容
        echo gzencode($content);
        
        // 删除解压后的文件
        unlink($file_to_unzip);
    } else {
        echo 'Failed to open ZIP file.';
    }
} else {
    echo 'No MD5 provided.';
}
?>

我的需求是：文件A在服务端以压缩后的ZIP文件B保存，用户请求下载时，服务端将B解压成A，然后将A以压缩编码发送给客户端，客户端应该是由浏览器自动还原为未压缩的A。我希望以一个简单的PHP脚本实现。例如请求main.php?md5=xxxyyyzzz时，脚本自动在D目录下查找xxxyyyzzz.zip（即B）

你可以使用 PHP 的 ZipArchive 类来解压缩 ZIP 文件，然后使用 ob_start() 和 ob_end_flush() 函数来捕获并发送解压缩后的文件内容。以下是一个简单的 PHP 脚本示例：

在这个脚本中，我们首先检查 md5 参数是否存在。如果存在，我们就打开对应的 ZIP 文件，解压缩其中的文件，然后读取并发送文件内容。我们使用 ob_start() 和 ob_end_flush() 函数来捕获和发送输出，这样我们就可以在发送文件内容之前设置响应头。我们设置 Content-Encoding 响应头为 gzip，这样浏览器就会自动解压缩响应体。我们还设置 Content-Disposition 响应头，使得浏览器将响应体保存为文件。最后，我们删除解压缩后的文件。